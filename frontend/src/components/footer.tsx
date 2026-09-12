import Link from "next/link";
import { Sparkles } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t bg-muted/40 py-8 mt-auto">
      <div className="container mx-auto px-4 sm:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-foreground">NooBlog</span>
          <span>— Built with FastAPI, Prisma & Next.js</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1 text-xs">
            <Sparkles className="h-3.5 w-3.5 text-primary" /> Powered by Google Gemini AI
          </span>
          <Link
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            className="hover:text-foreground underline underline-offset-4 text-xs"
          >
            API Docs
          </Link>
        </div>
      </div>
    </footer>
  );
}
