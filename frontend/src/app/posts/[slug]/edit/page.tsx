"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { api } from "@/lib/api";
import { Post } from "@/types";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Loader2, ArrowLeft, Save } from "lucide-react";
import { cn } from "cn";

export default function EditPostPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const { user, isLoading: isAuthLoading } = useAuth();
  const [post, setPost] = useState<Post | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [coverImage, setCoverImage] = useState("");
  const [tagInput, setTagInput] = useState("");
  const [isLoadingPost, setIsLoadingPost] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!slug) return;

    const loadPost = async () => {
      setIsLoadingPost(true);
      try {
        const data = await api.getPostBySlug(slug);
        setPost(data);
        setTitle(data.title);
        setContent(data.content);
        setCoverImage(data.cover_image || "");
        setTagInput(data.tags?.join(", ") || "");
      } catch {
        toast.error("Failed to load article");
      } finally {
        setIsLoadingPost(false);
      }
    };

    loadPost();
  }, [slug]);

  if (isAuthLoading || isLoadingPost) {
    return (
      <div className="container max-w-2xl mx-auto px-4 py-16 text-center">
        <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary" />
        <p className="text-sm text-muted-foreground mt-2">Loading editor...</p>
      </div>
    );
  }

  if (!user || (post && post.author?.id !== user.id)) {
    return (
      <div className="container max-w-md mx-auto px-4 py-16 text-center space-y-4">
        <h2 className="text-2xl font-bold">Unauthorized</h2>
        <p className="text-muted-foreground text-sm">
          You are not authorized to edit this article.
        </p>
        <Link href="/" className={buttonVariants()}>
          Back to Home
        </Link>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="container max-w-md mx-auto px-4 py-16 text-center space-y-4">
        <h2 className="text-2xl font-bold">Article not found</h2>
        <Link href="/" className={buttonVariants()}>
          Back to Home
        </Link>
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
      const updated = await api.updatePost(post.id, {
        title,
        content,
        cover_image: coverImage.trim() || undefined,
        tags,
      });

      toast.success("Article updated successfully!");
      router.push(`/posts/${updated.slug}`);
    } catch (err: any) {
      toast.error(err.message || "Failed to update article");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container max-w-3xl mx-auto px-4 py-10 space-y-6">
      <Link
        href={`/posts/${post.slug}`}
        className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "gap-2 text-muted-foreground")}
      >
        <ArrowLeft className="h-4 w-4" />
        <span>Back to article</span>
      </Link>

      <Card className="border-border/60 shadow-sm">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">Edit Article</CardTitle>
          <CardDescription>Make updates to your article and save changes.</CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <label htmlFor="title" className="text-sm font-medium">
                Article Title <span className="text-destructive">*</span>
              </label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                disabled={isSubmitting}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="coverImage" className="text-sm font-medium">
                Cover Image URL
              </label>
              <Input
                id="coverImage"
                type="url"
                value={coverImage}
                onChange={(e) => setCoverImage(e.target.value)}
                disabled={isSubmitting}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="tags" className="text-sm font-medium">
                Tags (Comma-separated)
              </label>
              <Input
                id="tags"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                disabled={isSubmitting}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="content" className="text-sm font-medium">
                Content <span className="text-destructive">*</span>
              </label>
              <Textarea
                id="content"
                rows={12}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                required
                disabled={isSubmitting}
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Link href={`/posts/${post.slug}`} className={buttonVariants({ variant: "outline" })}>
                Cancel
              </Link>
              <Button type="submit" disabled={isSubmitting} className="gap-2">
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" />
                    <span>Save Changes</span>
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </form>
      </Card>
    </div>
  );
}
