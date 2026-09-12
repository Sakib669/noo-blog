"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Post } from "@/types";
import { api } from "@/lib/api";
import { PostCard } from "@/components/post-card";
import { Input } from "@/components/ui/input";
import { Button, buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Search, Sparkles, PenSquare, BookOpen, AlertCircle } from "lucide-react";
import { cn } from "cn";

export default function HomePage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchPosts = async (search?: string, tag?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getPosts({
        search: search || undefined,
        tag: tag || undefined,
      });
      setPosts(data);
    } catch {
      setError("Could not load posts. Make sure the backend server is running.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchPosts(searchQuery, selectedTag || undefined);
  };

  const handleTagClick = (tag: string) => {
    const newTag = selectedTag === tag ? null : tag;
    setSelectedTag(newTag);
    fetchPosts(searchQuery, newTag || undefined);
  };

  // Collect popular tags from current posts
  const allTags = Array.from(new Set(posts.flatMap((p) => p.tags || []))).slice(0, 10);

  return (
    <div className="container mx-auto px-4 sm:px-8 py-10 space-y-12">
      {/* Hero section */}
      <section className="text-center max-w-3xl mx-auto space-y-4 pt-6 pb-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-semibold">
          <Sparkles className="h-3.5 w-3.5" /> Next-Gen AI Blogging
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">
          Read, write, and summarize with{" "}
          <span className="bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
            AI intelligence
          </span>
        </h1>
        <p className="text-lg text-muted-foreground">
          Discover insightful articles powered by FastAPI, Prisma, and Google Gemini AI summarization.
        </p>

        {/* Search bar */}
        <form onSubmit={handleSearch} className="flex max-w-lg mx-auto gap-2 pt-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search posts by title or content..."
              className="pl-9"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <Button type="submit">Search</Button>
        </form>

        {/* Tag pills */}
        {allTags.length > 0 && (
          <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
            <span className="text-xs text-muted-foreground mr-1">Popular:</span>
            {allTags.map((tag) => (
              <Badge
                key={tag}
                variant={selectedTag === tag ? "default" : "secondary"}
                className="cursor-pointer text-xs"
                onClick={() => handleTagClick(tag)}
              >
                #{tag}
              </Badge>
            ))}
            {selectedTag && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs text-muted-foreground"
                onClick={() => {
                  setSelectedTag(null);
                  fetchPosts(searchQuery, undefined);
                }}
              >
                Clear filter
              </Button>
            )}
          </div>
        )}
      </section>

      {/* Main content */}
      <section className="space-y-6">
        <div className="flex items-center justify-between border-b pb-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">
              {selectedTag ? `Articles tagged #${selectedTag}` : "Latest Articles"}
            </h2>
            <p className="text-sm text-muted-foreground">
              {posts.length} {posts.length === 1 ? "article" : "articles"} published
            </p>
          </div>
          <Link
            href="/posts/new"
            className={cn(buttonVariants({ variant: "outline", size: "sm" }), "gap-2")}
          >
            <PenSquare className="h-4 w-4" />
            <span>Create Post</span>
          </Link>
        </div>

        {error && (
          <div className="flex items-center gap-3 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <div className="text-sm">
              <p className="font-semibold">Failed to connect to backend</p>
              <p className="text-destructive/80">{error}</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="ml-auto bg-background text-foreground"
              onClick={() => fetchPosts(searchQuery, selectedTag || undefined)}
            >
              Retry
            </Button>
          </div>
        )}

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div
                key={i}
                className="h-72 rounded-xl border border-border/40 bg-muted/30 animate-pulse flex flex-col p-6 space-y-4"
              >
                <div className="h-4 bg-muted rounded w-1/4" />
                <div className="h-6 bg-muted rounded w-3/4" />
                <div className="h-16 bg-muted rounded w-full" />
                <div className="mt-auto h-4 bg-muted rounded w-1/2" />
              </div>
            ))}
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-16 border rounded-xl border-dashed border-border/80 space-y-4">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
              <BookOpen className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold">No articles found</h3>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto">
              {searchQuery || selectedTag
                ? "No articles matched your filter criteria. Try clearing search keywords or filters."
                : "Be the first to publish a post and try AI summarization!"}
            </p>
            <div className="flex justify-center gap-3 pt-2">
              {(searchQuery || selectedTag) && (
                <Button
                  variant="outline"
                  onClick={() => {
                    setSearchQuery("");
                    setSelectedTag(null);
                    fetchPosts();
                  }}
                >
                  Clear Search
                </Button>
              )}
              <Link href="/posts/new" className={buttonVariants()}>
                Write an article
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {posts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
