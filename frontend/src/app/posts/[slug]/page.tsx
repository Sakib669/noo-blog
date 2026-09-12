"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Comment, Post } from "@/types";
import { api } from "@/lib/api";
import { useAuth } from "@/context/auth-context";
import { Button, buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import {
  Sparkles,
  Calendar,
  Eye,
  Edit,
  Trash2,
  ArrowLeft,
  Loader2,
  MessageSquare,
  Send,
  Share2,
} from "lucide-react";
import { cn } from "cn";

export default function PostDetailPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const { user } = useAuth();
  const [post, setPost] = useState<Post | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [isSubmittingComment, setIsSubmittingComment] = useState(false);
  const [isDeletingPost, setIsDeletingPost] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  useEffect(() => {
    if (!slug) return;

    const loadData = async () => {
      setIsLoading(true);
      try {
        const postData = await api.getPostBySlug(slug);
        setPost(postData);

        const commentsData = await api.getComments(postData.id);
        setComments(commentsData);
      } catch {
        toast.error("Could not load the article");
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [slug]);

  const handleSummarize = async () => {
    if (!post) return;
    setIsSummarizing(true);
    try {
      const updatedPost = await api.summarizePost(post.id, true);
      setPost(updatedPost);
      toast.success("AI Summary generated successfully!");
    } catch (err: any) {
      toast.error(err.message || "Failed to generate AI summary");
    } finally {
      setIsSummarizing(false);
    }
  };

  const handleDeletePost = async () => {
    if (!post) return;
    setIsDeletingPost(true);
    try {
      await api.deletePost(post.id);
      toast.success("Article deleted successfully");
      router.push("/");
    } catch (err: any) {
      toast.error(err.message || "Failed to delete article");
    } finally {
      setIsDeletingPost(false);
      setDeleteDialogOpen(false);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!post || !newComment.trim()) return;

    setIsSubmittingComment(true);
    try {
      const created = await api.createComment(post.id, newComment.trim());
      setComments([created, ...comments]);
      setNewComment("");
      toast.success("Comment posted");
    } catch (err: any) {
      toast.error(err.message || "Failed to post comment");
    } finally {
      setIsSubmittingComment(false);
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    try {
      await api.deleteComment(commentId);
      setComments(comments.filter((c) => c.id !== commentId));
      toast.success("Comment deleted");
    } catch (err: any) {
      toast.error(err.message || "Failed to delete comment");
    }
  };

  const handleShare = () => {
    if (typeof window !== "undefined") {
      navigator.clipboard.writeText(window.location.href);
      toast.success("Link copied to clipboard!");
    }
  };

  if (isLoading) {
    return (
      <div className="container max-w-3xl mx-auto px-4 py-16 flex flex-col items-center justify-center space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Loading article...</p>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="container max-w-2xl mx-auto px-4 py-16 text-center space-y-4">
        <h2 className="text-2xl font-bold">Article not found</h2>
        <p className="text-muted-foreground">The article you are looking for does not exist or has been removed.</p>
        <Link href="/" className={buttonVariants()}>
          Return to Home
        </Link>
      </div>
    );
  }

  const isAuthor = user && post.author?.id === user.id;
  const authorName = post.author?.full_name || "Anonymous";
  const authorInitials = authorName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  const formattedDate = new Date(post.created_at).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  return (
    <article className="container max-w-3xl mx-auto px-4 py-10 space-y-8">
      {/* Back button */}
      <div>
        <Link
          href="/"
          className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "gap-2 text-muted-foreground")}
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to articles</span>
        </Link>
      </div>

      {/* Header */}
      <header className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          {post.tags?.map((tag) => (
            <Badge key={tag} variant="secondary">
              #{tag}
            </Badge>
          ))}
          {!post.published && (
            <Badge variant="outline" className="border-amber-500 text-amber-600 bg-amber-50">
              Draft
            </Badge>
          )}
        </div>

        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight leading-tight">
          {post.title}
        </h1>

        {/* Author metadata & actions */}
        <div className="flex flex-wrap items-center justify-between gap-4 py-4 border-y border-border/60 text-sm">
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10">
              <AvatarImage src={post.author?.avatar || ""} alt={authorName} />
              <AvatarFallback>{authorInitials}</AvatarFallback>
            </Avatar>
            <div>
              <p className="font-semibold leading-none">{authorName}</p>
              <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {formattedDate}
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Eye className="h-3 w-3" />
                  {post.views} views
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleShare} className="gap-1 text-xs">
              <Share2 className="h-3.5 w-3.5" />
              <span>Share</span>
            </Button>

            {isAuthor && (
              <>
                <Link
                  href={`/posts/${post.slug}/edit`}
                  className={cn(buttonVariants({ variant: "outline", size: "sm" }), "gap-1 text-xs")}
                >
                  <Edit className="h-3.5 w-3.5" />
                  <span>Edit</span>
                </Link>

                <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                  <DialogTrigger
                    className={cn(buttonVariants({ variant: "destructive", size: "sm" }), "gap-1 text-xs cursor-pointer")}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    <span>Delete</span>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Delete Article</DialogTitle>
                      <DialogDescription>
                        Are you sure you want to delete this article? This action cannot be undone.
                      </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
                        Cancel
                      </Button>
                      <Button variant="destructive" onClick={handleDeletePost} disabled={isDeletingPost}>
                        {isDeletingPost ? "Deleting..." : "Delete Permanently"}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Cover image */}
      {post.cover_image && (
        <div className="rounded-xl overflow-hidden border border-border/40 max-h-96">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={post.cover_image} alt={post.title} className="w-full h-full object-cover" />
        </div>
      )}

      {/* Gemini AI Summary Box */}
      {(post.summary || isAuthor) && (
        <Card className="bg-primary/5 border-primary/20 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2 font-semibold text-primary">
                <Sparkles className="h-4 w-4" />
                <span>AI Key Takeaways (Google Gemini)</span>
              </CardTitle>
              {isAuthor && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSummarize}
                  disabled={isSummarizing}
                  className="gap-1 text-xs border-primary/30 hover:bg-primary/10"
                >
                  {isSummarizing ? (
                    <>
                      <Loader2 className="h-3 w-3 animate-spin" />
                      <span>Summarizing...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-3 w-3" />
                      <span>{post.summary ? "Regenerate" : "Generate"}</span>
                    </>
                  )}
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {post.summary ? (
              <p className="text-sm leading-relaxed text-foreground/90">{post.summary}</p>
            ) : (
              <p className="text-xs text-muted-foreground italic">
                No AI summary generated yet. Click &quot;Generate&quot; to summarize this post with Gemini AI.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Post body content */}
      <section className="prose prose-neutral dark:prose-invert max-w-none text-base leading-relaxed space-y-4">
        {post.content.split("\n\n").map((paragraph, idx) => (
          <p key={idx} className="text-foreground/90">
            {paragraph}
          </p>
        ))}
      </section>

      <Separator />

      {/* Comments section */}
      <section className="space-y-6 pt-4">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-primary" />
          <h3 className="text-xl font-bold tracking-tight">
            Responses ({comments.length})
          </h3>
        </div>

        {/* Add comment form */}
        {user ? (
          <form onSubmit={handleAddComment} className="space-y-3">
            <Textarea
              placeholder="What are your thoughts on this article?"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              rows={3}
              required
            />
            <div className="flex justify-end">
              <Button type="submit" size="sm" disabled={isSubmittingComment || !newComment.trim()} className="gap-2">
                {isSubmittingComment ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Posting...</span>
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    <span>Respond</span>
                  </>
                )}
              </Button>
            </div>
          </form>
        ) : (
          <Card className="bg-muted/40 p-4 text-center text-sm">
            <p className="text-muted-foreground">
              <Link href="/login" className="text-primary font-semibold underline underline-offset-4">
                Log in
              </Link>{" "}
              or{" "}
              <Link href="/register" className="text-primary font-semibold underline underline-offset-4">
                create an account
              </Link>{" "}
              to leave a response.
            </p>
          </Card>
        )}

        {/* Comment list */}
        <div className="space-y-4 pt-2">
          {comments.length === 0 ? (
            <p className="text-sm text-muted-foreground italic">No responses yet. Start the conversation!</p>
          ) : (
            comments.map((comment) => {
              const cAuthor = comment.author?.full_name || "User";
              const cInitials = cAuthor
                .split(" ")
                .map((n) => n[0])
                .join("")
                .toUpperCase()
                .slice(0, 2);
              const cDate = new Date(comment.created_at).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              });
              const isCommentAuthor = user && comment.author?.id === user.id;

              return (
                <div key={comment.id} className="p-4 rounded-lg border border-border/50 bg-card space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Avatar className="h-7 w-7">
                        <AvatarImage src={comment.author?.avatar || ""} alt={cAuthor} />
                        <AvatarFallback className="text-[10px]">{cInitials}</AvatarFallback>
                      </Avatar>
                      <div>
                        <span className="text-xs font-semibold text-foreground">{cAuthor}</span>
                        <span className="text-[11px] text-muted-foreground ml-2">{cDate}</span>
                      </div>
                    </div>

                    {isCommentAuthor && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
                        onClick={() => handleDeleteComment(comment.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </div>
                  <p className="text-sm text-foreground/90 pl-9 whitespace-pre-line">{comment.content}</p>
                </div>
              );
            })
          )}
        </div>
      </section>
    </article>
  );
}
