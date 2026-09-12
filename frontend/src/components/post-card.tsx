import Link from "next/link";
import { Post } from "@/types";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Eye, Sparkles, Calendar } from "lucide-react";

interface PostCardProps {
  post: Post;
}

export function PostCard({ post }: PostCardProps) {
  const authorName = post.author?.full_name || "Anonymous";
  const authorUsername = post.author?.username || "anonymous";
  const initials = authorName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  const formattedDate = new Date(post.created_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <Card className="flex flex-col h-full overflow-hidden hover:shadow-md transition-shadow border-border/60">
      {post.cover_image && (
        <div className="relative h-48 w-full overflow-hidden bg-muted">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={post.cover_image}
            alt={post.title}
            className="h-full w-full object-cover transition-transform hover:scale-105 duration-300"
          />
        </div>
      )}

      <CardHeader className="space-y-2 pb-2">
        <div className="flex flex-wrap items-center gap-2">
          {post.tags?.map((tag) => (
            <Badge key={tag} variant="secondary" className="text-xs font-normal">
              #{tag}
            </Badge>
          ))}
          {post.summary && (
            <Badge variant="outline" className="text-xs font-normal border-primary/30 text-primary gap-1">
              <Sparkles className="h-3 w-3" /> AI Summary
            </Badge>
          )}
        </div>

        <Link href={`/posts/${post.slug}`} className="group">
          <h2 className="text-xl font-bold tracking-tight group-hover:text-primary transition-colors line-clamp-2">
            {post.title}
          </h2>
        </Link>
      </CardHeader>

      <CardContent className="flex-1 pb-4">
        <p className="text-sm text-muted-foreground line-clamp-3">
          {post.summary || post.content}
        </p>
      </CardContent>

      <CardFooter className="pt-0 flex items-center justify-between border-t border-border/40 py-3 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <Avatar className="h-6 w-6">
            <AvatarImage src={post.author?.avatar || ""} alt={authorName} />
            <AvatarFallback className="text-[10px]">{initials}</AvatarFallback>
          </Avatar>
          <span className="font-medium text-foreground">{authorName}</span>
          <span>•</span>
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {formattedDate}
          </span>
        </div>

        <div className="flex items-center gap-1">
          <Eye className="h-3.5 w-3.5" />
          <span>{post.views}</span>
        </div>
      </CardFooter>
    </Card>
  );
}
