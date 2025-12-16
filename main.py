#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import boto3
import requests
import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Optional OpenAI
try:
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None  # type: ignore


# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("ig_autoposter")


# ----------------------------
# Config models
# ----------------------------
@dataclass
class InstagramAccount:
    name: str
    ig_user_id: str
    access_token: str
    api_version: str = "v20.0"

@dataclass
class S3Config:
    endpoint_url: str
    region: str
    bucket: str
    access_key_id: str
    secret_access_key: str
    state_key: str

@dataclass
class OpenAIConfig:
    enabled: bool
    api_key: str
    model: str = "gpt-4o-mini"
    max_caption_chars: int = 1800

@dataclass
class BrandConfig:
    brand_key: str
    instagram: InstagramAccount
    s3_prefix_posts: str
    s3_prefix_stories: str
    language: str
    tone: str
    hashtags: List[str]
    schedule_posts: List[str]
    schedule_stories: List[str]
    stories_per_run: int = 1


# ----------------------------
# S3 helpers
# ----------------------------
def make_s3_client(s3cfg: S3Config):
    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=s3cfg.endpoint_url,
        region_name=s3cfg.region,
        aws_access_key_id=s3cfg.access_key_id,
        aws_secret_access_key=s3cfg.secret_access_key,
    )

def list_s3_objects(s3, bucket: str, prefix: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    token = None
    while True:
        kwargs = dict(Bucket=bucket, Prefix=prefix, MaxKeys=1000)
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kwargs)
        out.extend(resp.get("Contents", []))
        if resp.get("IsTruncated"):
            token = resp.get("NextContinuationToken")
        else:
            break
    return out

def presign_url(s3, bucket: str, key: str, expires: int = 3600) -> str:
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires,
    )

def read_state(s3, s3cfg: S3Config) -> Dict[str, Any]:
    try:
        resp = s3.get_object(Bucket=s3cfg.bucket, Key=s3cfg.state_key)
        return json.loads(resp["Body"].read().decode("utf-8"))
    except Exception:
        return {}

def write_state(s3, s3cfg: S3Config, state: Dict[str, Any]) -> None:
    body = json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8")
    s3.put_object(
        Bucket=s3cfg.bucket,
        Key=s3cfg.state_key,
        Body=body,
        ContentType="application/json",
    )


# ----------------------------
# Instagram API
# ----------------------------
def ig_api_url(api_version: str, path: str) -> str:
    return f"https://graph.facebook.com/{api_version}/{path.lstrip('/')}"

def ig_create_media_container(
    ig: InstagramAccount,
    *,
    image_url: Optional[str] = None,
    video_url: Optional[str] = None,
    caption: Optional[str] = None,
    media_type: Optional[str] = None,
) -> str:
    url = ig_api_url(ig.api_version, f"/{ig.ig_user_id}/media")
    payload: Dict[str, Any] = {"access_token": ig.access_token}
    if image_url:
        payload["image_url"] = image_url
    if video_url:
        payload["video_url"] = video_url
    if caption:
        payload["caption"] = caption
    if media_type:
        payload["media_type"] = media_type

    r = requests.post(url, data=payload, timeout=60)
    r.raise_for_status()
    cid = r.json().get("id")
    if not cid:
        raise RuntimeError(f"IG create container failed: {r.text}")
    return cid

def ig_publish_media(ig: InstagramAccount, creation_id: str) -> str:
    url = ig_api_url(ig.api_version, f"/{ig.ig_user_id}/media_publish")
    payload = {"creation_id": creation_id, "access_token": ig.access_token}
    r = requests.post(url, data=payload, timeout=60)
    r.raise_for_status()
    mid = r.json().get("id")
    if not mid:
        raise RuntimeError(f"IG publish failed: {r.text}")
    return mid


# ----------------------------
# OpenAI captions
# ----------------------------
def build_caption_prompt(brand: BrandConfig) -> str:
    lang = "Ukrainian" if brand.language.startswith("uk") else "Russian"
    hashtags = " ".join(brand.hashtags)
    return (
        f"Write an Instagram caption in {lang}.\n"
        f"Brand: {brand.instagram.name}\n"
        f"Tone: {brand.tone}\n"
        f"Rules:\n"
        f"- No invented facts\n"
        f"- Natural style\n"
        f"- Soft CTA\n"
        f"- Hashtags at end: {hashtags}\n"
    )

def generate_caption(cfg: OpenAIConfig, brand: BrandConfig, url: str) -> str:
    if not cfg.enabled or OpenAI is None:
        return "✨"

    client = OpenAI(api_key=cfg.api_key)
    prompt = build_caption_prompt(brand)

    resp = client.chat.completions.create(
        model=cfg.model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": url}},
            ],
        }],
        temperature=0.8,
    )
    text = (resp.choices[0].message.content or "✨").strip()
    return text[: cfg.max_caption_chars]


# ----------------------------
# Content selection
# ----------------------------
IMAGE_EXT = (".jpg", ".jpeg", ".png")
VIDEO_EXT = (".mp4", ".mov")

def pick_next_media(objects: List[Dict[str, Any]], used: set[str]) -> Optional[str]:
    candidates = [
        o["Key"] for o in objects
        if o.get("Key")
        and not o["Key"].endswith("/")
        and o["Key"] not in used
        and o["Key"].lower().endswith(IMAGE_EXT + VIDEO_EXT)
    ]
    return random.choice(candidates) if candidates else None


# ----------------------------
# Jobs
# ----------------------------
async def publish_post(brand: BrandConfig, s3cfg: S3Config, oai: OpenAIConfig):
    s3 = make_s3_client(s3cfg)
    state = read_state(s3, s3cfg)
    bstate = state.setdefault(brand.brand_key, {"posts": [], "stories": []})

    objs = list_s3_objects(s3, s3cfg.bucket, brand.s3_prefix_posts + "/")
    key = pick_next_media(objs, set(bstate["posts"]))
    if not key:
        logger.info(f"[{brand.brand_key}] no new posts")
        return

    url = presign_url(s3, s3cfg.bucket, key)
    caption = generate_caption(oai, brand, url)

    if key.lower().endswith(VIDEO_EXT):
        cid = ig_create_media_container(brand.instagram, video_url=url, caption=caption)
    else:
        cid = ig_create_media_container(brand.instagram, image_url=url, caption=caption)

    mid = ig_publish_media(brand.instagram, cid)
    bstate["posts"].append(key)
    write_state(s3, s3cfg, state)

    logger.info(f"[{brand.brand_key}] POST published {mid}")

async def publish_stories(brand: BrandConfig, s3cfg: S3Config):
    s3 = make_s3_client(s3cfg)
    state = read_state(s3, s3cfg)
    bstate = state.setdefault(brand.brand_key, {"posts": [], "stories": []})

    objs = list_s3_objects(s3, s3cfg.bucket, brand.s3_prefix_stories + "/")
    used = set(bstate["stories"])
    published = 0

    for _ in range(brand.stories_per_run):
        key = pick_next_media(objs, used)
        if not key:
            break

        url = presign_url(s3, s3cfg.bucket, key)
        if key.lower().endswith(VIDEO_EXT):
            cid = ig_create_media_container(brand.instagram, video_url=url, media_type="STORIES")
        else:
            cid = ig_create_media_container(brand.instagram, image_url=url, media_type="STORIES")

        ig_publish_media(brand.instagram, cid)
        bstate["stories"].append(key)
        used.add(key)
        published += 1
        await asyncio.sleep(random.uniform(3, 6))

    if published:
        write_state(s3, s3cfg, state)
        logger.info(f"[{brand.brand_key}] {published} stories published")


# ----------------------------
# Scheduler
# ----------------------------
def parse_cron(expr: str) -> CronTrigger:
    minute, hour, day, month, dow = expr.split()
    return CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=dow)

def load_config(path: str) -> Tuple[S3Config, OpenAIConfig, List[BrandConfig]]:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    s3cfg = S3Config(**raw["s3"])
    oai = OpenAIConfig(**raw.get("openai", {}))

    brands: List[BrandConfig] = []
    for b in raw["brands"]:
        ig = InstagramAccount(**b["instagram"])
        brands.append(BrandConfig(instagram=ig, **{k: v for k, v in b.items() if k != "instagram"}))

    return s3cfg, oai, brands


async def main():
    s3cfg, oai, brands = load_config(os.getenv("CONFIG_PATH", "config.yaml"))
    scheduler = AsyncIOScheduler(timezone=os.getenv("TZ", "Europe/Kyiv"))

    for b in brands:
        for c in b.schedule_posts:
            scheduler.add_job(publish_post, parse_cron(c), args=[b, s3cfg, oai])
        for c in b.schedule_stories:
            scheduler.add_job(publish_stories, parse_cron(c), args=[b, s3cfg])

        logger.info(f"[{b.brand_key}] jobs registered")

    scheduler.start()
    logger.info("Scheduler started")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
