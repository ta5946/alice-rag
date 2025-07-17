import os
import json
import time
from datetime import datetime
from tqdm import tqdm
from src.chatbot.mattermost_utils import MATTERMOST_DRIVER
from src.scraper.question_extractor import qe_pipeline
from dotenv import load_dotenv

load_dotenv()


MATTERMOST_DRIVER.login()

def get_channel_posts(channel_id, start_timestamp):
    current_page = 0
    per_page = 100
    channel_posts = []

    while True:
        response = MATTERMOST_DRIVER.posts.get_posts_for_channel(
            channel_id,
            params={"page": current_page, "per_page": per_page}
        )
        posts = response.get("posts")
        if not posts:
            break # no more posts

        for post in posts.values():
            create_at = post.get("create_at")
            if create_at >= start_timestamp:
                channel_posts.append(post)

        current_page += 1
        time.sleep(0.2) # optional rate limit buffer

    sorted_posts = sorted(channel_posts, key=lambda p: p["create_at"])
    return sorted_posts

def group_consecutive_posts(posts):
    grouped_posts = []
    current_post = None

    for post in posts:
        if current_post is None or current_post["user_id"] != post["user_id"]:
            if current_post:
                grouped_posts.append(current_post)
            current_post = post
        else:
            current_post["message"] += "\n" + post["message"] # extend message field

    if current_post:
        grouped_posts.append(current_post)
    return grouped_posts


if __name__ == "__main__":
    channel_id = os.getenv("MATTERMOST_CHANNEL_ID")
    start_date = datetime(2020, 1, 1)
    start_timestamp = int(start_date.timestamp() * 1000)

    channel_posts = get_channel_posts(channel_id, start_timestamp) # 891 posts
    user_posts = [p for p in channel_posts if "system" not in p.get("type").lower()] # 735 posts
    grouped_posts = group_consecutive_posts(user_posts) # 538 posts
    final_posts = [p for p in grouped_posts if 0 < len(p["message"]) <= 10000] # 536 posts
    print("TOTAL POSTS:", len(final_posts))


    # load the existing question dataset
    json_path = os.path.join(os.path.dirname(__file__), "questions.json")

    existing_questions = []
    if os.path.exists(json_path) and os.path.getsize(json_path) > 0:
        with open(json_path, "r", encoding="utf-8") as json_file:
            existing_questions = json.load(json_file)
    existing_post_ids = {q["post_id"] for q in existing_questions}

    for post in tqdm(final_posts, desc="Extracting questions", unit="post"):
        try:
            if post["id"] in existing_post_ids: # already processed
                continue

            question = qe_pipeline(post["message"])
            if not question: # not a question
                continue

            json_object = {
                "source": "mattermost",
                "post_id": post["id"],
                "create_at": post["create_at"],
                "user_id": post["user_id"],
                "message": post["message"],
                "question": question
            }
            existing_questions.append(json_object)
            existing_post_ids.add(post["id"])
            with open(json_path, "w", encoding="utf-8") as json_file:
                json.dump(existing_questions, json_file, indent=4, ensure_ascii=False) # update dataset

        except Exception as error:
            print("Error processing post:", post["id"], error)
