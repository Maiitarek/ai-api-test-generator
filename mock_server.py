"""
Local mock API server — no internet required.
Start with: python mock_server.py
Docs at:    http://localhost:8000/docs
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="Mock API Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

POSTS = [{"id": i, "title": f"Post {i}", "body": f"Body of post {i}", "userId": 1} for i in range(1, 11)]
USERS = [{"id": i, "name": f"User {i}", "email": f"user{i}@example.com", "job": "QA Engineer"} for i in range(1, 6)]
COMMENTS = [{"id": i, "postId": (i % 5) + 1, "name": f"Comment {i}", "body": f"Body {i}"} for i in range(1, 11)]
next_post_id = 11


class PostCreate(BaseModel):
    title: str
    body: str
    userId: int

class PostUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    userId: Optional[int] = None


@app.get("/posts")
def list_posts(limit: int = 10): return POSTS[:limit]

@app.post("/posts", status_code=201)
def create_post(post: PostCreate):
    global next_post_id
    new_post = {"id": next_post_id, **post.model_dump()}
    POSTS.append(new_post); next_post_id += 1
    return new_post

@app.get("/posts/{post_id}")
def get_post(post_id: int):
    post = next((p for p in POSTS if p["id"] == post_id), None)
    if not post: raise HTTPException(404, "Post not found")
    return post

@app.put("/posts/{post_id}")
def update_post(post_id: int, post: PostCreate):
    existing = next((p for p in POSTS if p["id"] == post_id), None)
    if not existing: raise HTTPException(404, "Post not found")
    existing.update(post.model_dump()); return existing

@app.patch("/posts/{post_id}")
def patch_post(post_id: int, post: PostUpdate):
    existing = next((p for p in POSTS if p["id"] == post_id), None)
    if not existing: raise HTTPException(404, "Post not found")
    for k, v in post.model_dump(exclude_none=True).items(): existing[k] = v
    return existing

@app.delete("/posts/{post_id}")
def delete_post(post_id: int):
    existing = next((p for p in POSTS if p["id"] == post_id), None)
    if not existing: raise HTTPException(404, "Post not found")
    POSTS.remove(existing); return {"message": f"Post {post_id} deleted"}

@app.get("/users")
def list_users(limit: int = 10): return USERS[:limit]

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = next((u for u in USERS if u["id"] == user_id), None)
    if not user: raise HTTPException(404, "User not found")
    return user

@app.get("/comments")
def list_comments(postId: Optional[int] = None, limit: int = 10):
    if postId: return [c for c in COMMENTS if c["postId"] == postId][:limit]
    return COMMENTS[:limit]

@app.get("/health")
def health(): return {"status": "ok"}


if __name__ == "__main__":
    print("\nMock API server starting at http://localhost:8000")
    print("Docs: http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
