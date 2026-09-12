"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { api } from "@/lib/api";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Loader2, PenSquare, ArrowLeft } from "lucide-react";
import { cn } from "cn";

export default function NewPostPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [coverImage, setCoverImage] = useState("");
  const [tagInput, setTagInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isAuthLoading) {
    return (
      <div className="container max-w-2xl mx-auto px-4 py-16 text-center">
        <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="container max-w-md mx-auto px-4 py-16 text-center space-y-4">
        <h2 className="text-2xl font-bold">Authentication Required</h2>
        <p className="text-muted-foreground text-sm">
          You must be logged in to create and publish articles.
        </p>
        <div className="flex justify-center gap-3 pt-2">
          <Link href="/login" className={buttonVariants()}>
            Log in
          </Link>
          <Link href="/register" className={buttonVariants({ variant: "outline" })}>
            Sign up
          </Link>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (title.length < 3) {
      toast.error("Title must be at least 3 characters");
      return;
    }

    if (content.length < 10) {
      toast.error("Content must be at least 10 characters");
      return;
    }

    const tags = tagInput
      .split(",")
      .map((t) => t.trim().toLowerCase().replace(/^#/, ""))
      .filter(Boolean);

    setIsSubmitting(true);
    try {
      const created = await api.createPost({
        title,
        content,
        cover_image: coverImage.trim() || undefined,
        tags,
      });

      toast.success("Post created successfully!");
      router.push(`/posts/${created.slug}`);
    } catch (err: any) {
      toast.error(err.message || "Failed to create post");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container max-w-3xl mx-auto px-4 py-10 space-y-6">
      <Link
        href="/"
        className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "gap-2 text-muted-foreground")}
      >
        <ArrowLeft className="h-4 w-4" />
        <span>Back to articles</span>
      </Link>

      <Card className="border-border/60 shadow-sm">
        <CardHeader>
          <div className="flex items-center gap-2 text-primary font-semibold text-sm mb-1">
            <PenSquare className="h-4 w-4" />
            <span>Create New Article</span>
          </div>
          <CardTitle className="text-2xl font-bold">Write Your Story</CardTitle>
          <CardDescription>
            Share your knowledge, tutorials, or perspectives with the NooBlog community.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <label htmlFor="title" className="text-sm font-medium">
                Article Title <span className="text-destructive">*</span>
              </label>
              <Input
                id="title"
                placeholder="e.g. Getting Started with FastAPI and Next.js"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                disabled={isSubmitting}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="coverImage" className="text-sm font-medium">
                Cover Image URL (Optional)
              </label>
              <Input
                id="coverImage"
                type="url"
                placeholder="https://images.unsplash.com/..."
                value={coverImage}
                onChange={(e) => setCoverImage(e.target.value)}
                disabled={isSubmitting}
              />
              <p className="text-xs text-muted-foreground">Paste a direct image URL for the article header.</p>
            </div>

            <div className="space-y-2">
              <label htmlFor="tags" className="text-sm font-medium">
                Tags (Comma-separated)
              </label>
              <Input
                id="tags"
                placeholder="python, fastapi, nextjs, ai"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                disabled={isSubmitting}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="content" className="text-sm font-medium">
                Content (Markdown or Plain Text) <span className="text-destructive">*</span>
              </label>
              <Textarea
                id="content"
                placeholder="Write your article content here..."
                rows={12}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                required
                disabled={isSubmitting}
              />
              <p className="text-xs text-muted-foreground">
                Minimum 10 characters. Once created, you can generate Gemini AI summaries directly from the post page.
              </p>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Link href="/" className={buttonVariants({ variant: "outline" })}>
                Cancel
              </Link>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Publishing...
                  </>
                ) : (
                  "Publish Article"
                )}
              </Button>
            </div>
          </CardContent>
        </form>
      </Card>
    </div>
  );
}
