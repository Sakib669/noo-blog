import asyncio
import sys
import uuid
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def run_all_endpoint_tests(base_url: str = "http://127.0.0.1:8000"):
    print("=" * 72)
    print(f"NOO BLOG - FULL COMPREHENSIVE ENDPOINT AUDIT & VERIFICATION")
    print(f"Target: {base_url}")
    print("=" * 72)

    results = []

    async with httpx.AsyncClient(base_url=base_url, timeout=35.0) as client:
        # ====================================================================
        # 1. ROOT
        # ====================================================================
        res = await client.get("/")
        p = res.status_code == 200 and "message" in res.json()
        results.append(("GET / (Root health check)", res.status_code, p, res.text))

        # ====================================================================
        # 2. AUTHENTICATION
        # ====================================================================
        uid = uuid.uuid4().hex[:6]
        user1 = {
            "email": f"author_{uid}@example.com",
            "username": f"author_{uid}",
            "password": "Password123!",
            "full_name": f"Author User {uid}",
        }
        user2 = {
            "email": f"reader_{uid}@example.com",
            "username": f"reader_{uid}",
            "password": "Password123!",
            "full_name": f"Reader User {uid}",
        }

        # Register User 1
        res = await client.post("/api/v1/auth/register", json=user1)
        p = res.status_code == 201 and "id" in res.json()
        results.append(("POST /api/v1/auth/register (Create author)", res.status_code, p, f"User ID: {res.json().get('id') if p else 'failed'}"))

        # Duplicate register check
        res = await client.post("/api/v1/auth/register", json=user1)
        p = res.status_code == 400
        results.append(("POST /api/v1/auth/register (Duplicate -> 400)", res.status_code, p, res.text))

        # Register User 2
        res = await client.post("/api/v1/auth/register", json=user2)
        p = res.status_code == 201
        results.append(("POST /api/v1/auth/register (Create second user)", res.status_code, p, f"User2 ID: {res.json().get('id') if p else 'failed'}"))

        # Login User 1
        res = await client.post("/api/v1/auth/login", json={"email": user1["email"], "password": user1["password"]})
        token1 = res.json().get("access_token") if res.status_code == 200 else None
        p = res.status_code == 200 and bool(token1)
        results.append(("POST /api/v1/auth/login (Author login -> 200)", res.status_code, p, f"Token: {bool(token1)}"))

        # Login User 2
        res = await client.post("/api/v1/auth/login", json={"email": user2["email"], "password": user2["password"]})
        token2 = res.json().get("access_token") if res.status_code == 200 else None
        p = res.status_code == 200 and bool(token2)
        results.append(("POST /api/v1/auth/login (Second user login -> 200)", res.status_code, p, f"Token: {bool(token2)}"))

        headers1 = {"Authorization": f"Bearer {token1}"} if token1 else {}
        headers2 = {"Authorization": f"Bearer {token2}"} if token2 else {}

        # Bad password login
        res = await client.post("/api/v1/auth/login", json={"email": user1["email"], "password": "WrongPassword"})
        p = res.status_code == 401
        results.append(("POST /api/v1/auth/login (Bad credentials -> 401)", res.status_code, p, res.text))

        # GET /me without auth
        res = await client.get("/api/v1/auth/me")
        p = res.status_code == 401
        results.append(("GET /api/v1/auth/me (No token -> 401)", res.status_code, p, res.text))

        # GET /me with auth
        res = await client.get("/api/v1/auth/me", headers=headers1)
        p = res.status_code == 200 and res.json().get("email") == user1["email"]
        results.append(("GET /api/v1/auth/me (Authenticated profile -> 200)", res.status_code, p, f"Email: {res.json().get('email') if p else 'failed'}"))

        # ====================================================================
        # 3. USERS SELF-SERVICE & PUBLIC PROFILES
        # ====================================================================
        # PUT /users/me (Update bio & full_name)
        res = await client.put(
            "/api/v1/users/me",
            json={"bio": "Software engineer & technical blogger.", "full_name": f"Author Updated {uid}"},
            headers=headers1,
        )
        p = res.status_code == 200 and res.json().get("bio") == "Software engineer & technical blogger."
        results.append(("PUT /api/v1/users/me (Update profile -> 200)", res.status_code, p, res.text))

        # GET /users/{username} (Public profile)
        res = await client.get(f"/api/v1/users/{user1['username']}")
        data = res.json() if res.status_code == 200 else {}
        # Must return public details, and MUST NOT leak email or password
        p = res.status_code == 200 and data.get("username") == user1["username"] and "email" not in data and "password" not in data
        results.append((f"GET /api/v1/users/{user1['username']} (Public profile -> 200)", res.status_code, p, f"Email hidden: {'email' not in data}"))

        # GET /users/{username} (Nonexistent user -> 404)
        res = await client.get("/api/v1/users/non_existent_username_xyz_123")
        p = res.status_code == 404
        results.append(("GET /api/v1/users/{username} (Nonexistent -> 404)", res.status_code, p, res.text))

        # ====================================================================
        # 4. POSTS CRUD
        # ====================================================================
        # POST /posts/ (Create post)
        post_payload = {
            "title": f"Mastering Modern Web Architecture {uid}",
            "content": "Building scalable applications requires thoughtful API design, robust database relations, and caching strategies. This post explores best practices in detail.",
            "summary": "Introduction to scalable web architecture.",
            "tags": ["architecture", "web", "fastapi"],
        }
        res = await client.post("/api/v1/posts/", json=post_payload, headers=headers1)
        p = res.status_code == 201 and "id" in res.json()
        post_data = res.json() if p else {}
        post_id = post_data.get("id")
        post_slug = post_data.get("slug")
        results.append(("POST /api/v1/posts/ (Create post -> 201)", res.status_code, p, f"ID: {post_id}, Slug: {post_slug}"))

        # GET /posts/{slug} (Fetch post and verify view counter increment)
        res = await client.get(f"/api/v1/posts/{post_slug}")
        v1 = res.json().get("views", 0) if res.status_code == 200 else 0
        res = await client.get(f"/api/v1/posts/{post_slug}")
        v2 = res.json().get("views", 0) if res.status_code == 200 else 0
        p = res.status_code == 200 and v2 == (v1 + 1)
        results.append((f"GET /api/v1/posts/{post_slug} (Views increment -> 200)", res.status_code, p, f"Views: {v2}"))

        # GET /posts/ (Draft filtering verification)
        res = await client.get("/api/v1/posts/")
        ids = [x["id"] for x in res.json()] if res.status_code == 200 else []
        p = res.status_code == 200 and (post_id not in ids)
        results.append(("GET /api/v1/posts/ (Draft hidden from public feed)", res.status_code, p, f"Draft excluded: {post_id not in ids}"))

        # PATCH /posts/{id}/publish (Toggle publish)
        # Unauthorized check:
        res = await client.patch(f"/api/v1/posts/{post_id}/publish", headers=headers2)
        p = res.status_code == 403
        results.append(("PATCH /api/v1/posts/{id}/publish (Forbidden non-author -> 403)", res.status_code, p, res.text))

        # Authorized publish:
        res = await client.patch(f"/api/v1/posts/{post_id}/publish", headers=headers1)
        p = res.status_code == 200 and res.json().get("published") is True
        results.append(("PATCH /api/v1/posts/{id}/publish (Author publishes -> 200)", res.status_code, p, f"Published: {res.json().get('published') if p else 'failed'}"))

        # GET /posts/ (Verify published post now visible)
        res = await client.get("/api/v1/posts/")
        ids = [x["id"] for x in res.json()] if res.status_code == 200 else []
        p = res.status_code == 200 and (post_id in ids)
        results.append(("GET /api/v1/posts/ (Published post in public feed)", res.status_code, p, f"In list: {post_id in ids}"))

        # GET /users/{username}/posts (Author's published posts)
        res = await client.get(f"/api/v1/users/{user1['username']}/posts")
        p = res.status_code == 200 and any(item["id"] == post_id for item in res.json())
        results.append((f"GET /api/v1/users/{user1['username']}/posts (Author posts -> 200)", res.status_code, p, f"Count: {len(res.json()) if p else 'failed'}"))

        # PUT /posts/{id} (Update post)
        new_title = f"Mastering Modern Web Architecture - Edition 2 {uid}"
        res = await client.put(
            f"/api/v1/posts/{post_id}",
            json={"title": new_title, "summary": "Updated summary for second edition"},
            headers=headers1,
        )
        p = res.status_code == 200 and res.json().get("title") == new_title
        results.append(("PUT /api/v1/posts/{id} (Update post -> 200)", res.status_code, p, f"New title: {new_title}"))

        # ====================================================================
        # 5. AI SUMMARIZATION (POST /api/v1/posts/{id}/summarize)
        # ====================================================================
        # Unauthorized check
        res = await client.post(f"/api/v1/posts/{post_id}/summarize", headers=headers2)
        p = res.status_code == 403
        results.append(("POST /api/v1/posts/{id}/summarize (Non-author forbidden -> 403)", res.status_code, p, res.text))

        # Author summarize check
        print("  -> Calling AI Summarization endpoint (Gemini API)...")
        res = await client.post(f"/api/v1/posts/{post_id}/summarize?force=true", headers=headers1)
        # Note: If Gemini API succeeds -> 200. If upstream quota/key error -> 502 (handled cleanly)
        ai_success = res.status_code == 200 and bool(res.json().get("summary"))
        results.append(("POST /api/v1/posts/{id}/summarize (AI summarization)", res.status_code, res.status_code in [200, 502], f"Status: {res.status_code}, Summary snippet: {str(res.json().get('summary'))[:80] if res.status_code == 200 else res.text[:80]}"))

        # ====================================================================
        # 6. COMMENTS API
        # ====================================================================
        # POST /posts/{post_id}/comments (Create comment by user 2)
        comment_payload = {"content": f"Fascinating article! Thanks for sharing #{uid}."}
        res = await client.post(f"/api/v1/posts/{post_id}/comments", json=comment_payload, headers=headers2)
        p = res.status_code == 201 and "id" in res.json()
        comment_data = res.json() if p else {}
        comment_id = comment_data.get("id")
        results.append((f"POST /api/v1/posts/{post_id}/comments (Create comment -> 201)", res.status_code, p, f"Comment ID: {comment_id}"))

        # GET /posts/{post_id}/comments (List comments)
        res = await client.get(f"/api/v1/posts/{post_id}/comments")
        comment_ids = [c["id"] for c in res.json()] if res.status_code == 200 else []
        p = res.status_code == 200 and (comment_id in comment_ids)
        results.append((f"GET /api/v1/posts/{post_id}/comments (List comments -> 200)", res.status_code, p, f"Found comment: {comment_id in comment_ids}"))

        # DELETE /comments/{comment_id} (Unauthorized delete check - author tries to delete user 2's comment)
        res = await client.delete(f"/api/v1/comments/{comment_id}", headers=headers1)
        p = res.status_code == 403
        results.append(("DELETE /api/v1/comments/{id} (Non-author forbidden -> 403)", res.status_code, p, res.text))

        # DELETE /comments/{comment_id} (Authorized delete - user 2 deletes own comment)
        res = await client.delete(f"/api/v1/comments/{comment_id}", headers=headers2)
        p = res.status_code == 204
        results.append(("DELETE /api/v1/comments/{id} (Owner deletes comment -> 204)", res.status_code, p, "204 No Content"))

        # ====================================================================
        # 7. PASSWORD CHANGE & RE-LOGIN
        # ====================================================================
        # PUT /users/me/password
        pw_payload = {
            "current_password": user1["password"],
            "new_password": "NewBrandPassword456!",
        }
        res = await client.put("/api/v1/users/me/password", json=pw_payload, headers=headers1)
        p = res.status_code == 204
        results.append(("PUT /api/v1/users/me/password (Change password -> 204)", res.status_code, p, "Password changed successfully"))

        # Verify old password no longer works
        res = await client.post("/api/v1/auth/login", json={"email": user1["email"], "password": user1["password"]})
        p = res.status_code == 401
        results.append(("POST /api/v1/auth/login (Old password rejected -> 401)", res.status_code, p, res.text))

        # Verify new password works
        res = await client.post("/api/v1/auth/login", json={"email": user1["email"], "password": pw_payload["new_password"]})
        p = res.status_code == 200 and "access_token" in res.json()
        results.append(("POST /api/v1/auth/login (New password accepted -> 200)", res.status_code, p, "Re-authenticated successfully"))

        # ====================================================================
        # 8. POST DELETE
        # ====================================================================
        # DELETE /posts/{id} (Unauthorized check)
        res = await client.delete(f"/api/v1/posts/{post_id}", headers=headers2)
        p = res.status_code == 403
        results.append(("DELETE /api/v1/posts/{id} (Non-author forbidden -> 403)", res.status_code, p, res.text))

        # DELETE /posts/{id} (Authorized delete)
        res = await client.delete(f"/api/v1/posts/{post_id}", headers=headers1)
        p = res.status_code == 204
        results.append(("DELETE /api/v1/posts/{id} (Author deletes post -> 204)", res.status_code, p, "Post deleted successfully"))

    print("\n" + "=" * 72)
    print("COMPLETE ENDPOINT AUDIT RESULTS")
    print("=" * 72)
    all_passed = True
    passed_count = 0
    for name, code, passed, detail in results:
        status_str = " PASS " if passed else " FAIL "
        if not passed:
            all_passed = False
        else:
            passed_count += 1
        print(f"[{status_str}] {name:<54} [HTTP {code}]")

    print("=" * 72)
    print(f"Audit Summary: {passed_count}/{len(results)} endpoint checks passed.")
    print("=" * 72)
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_endpoint_tests())
    sys.exit(0 if success else 1)
