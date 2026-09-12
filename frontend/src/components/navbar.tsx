"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Button, buttonVariants } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { PenSquare, Sparkles, User as UserIcon, LogOut } from "lucide-react";
import { cn } from "cn";

export function Navbar() {
  const { user, logout, isLoading } = useAuth();
  const router = useRouter();

  const getInitials = (name: string) => {
    return name
      ? name
          .split(" ")
          .map((n) => n[0])
          .join("")
          .toUpperCase()
          .slice(0, 2)
      : "U";
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-8">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2 font-bold text-xl tracking-tight">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-black">
            N
          </div>
          <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
            NooBlog
          </span>
          <span className="flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary">
            <Sparkles className="h-3 w-3" /> AI
          </span>
        </Link>

        {/* Right side items */}
        <div className="flex items-center gap-4">
          {!isLoading && (
            <>
              {user ? (
                <>
                  <Link
                    href="/posts/new"
                    className={cn(buttonVariants({ variant: "default", size: "sm" }), "gap-2")}
                  >
                    <PenSquare className="h-4 w-4" />
                    <span>Write</span>
                  </Link>

                  <DropdownMenu>
                    <DropdownMenuTrigger className="focus:outline-none cursor-pointer">
                      <Avatar className="h-9 w-9 ring-2 ring-primary/20 hover:ring-primary/40 transition">
                        <AvatarImage src={user.avatar || ""} alt={user.full_name} />
                        <AvatarFallback>{getInitials(user.full_name)}</AvatarFallback>
                      </Avatar>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-56">
                      <DropdownMenuLabel className="font-normal">
                        <div className="flex flex-col space-y-1">
                          <p className="text-sm font-medium leading-none">{user.full_name}</p>
                          <p className="text-xs leading-none text-muted-foreground">
                            @{user.username}
                          </p>
                        </div>
                      </DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => router.push("/profile")}
                        className="flex items-center gap-2 cursor-pointer"
                      >
                        <UserIcon className="h-4 w-4" />
                        <span>Profile & Settings</span>
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={logout}
                        className="text-destructive focus:text-destructive flex items-center gap-2 cursor-pointer"
                      >
                        <LogOut className="h-4 w-4" />
                        <span>Log out</span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </>
              ) : (
                <div className="flex items-center gap-2">
                  <Link
                    href="/login"
                    className={buttonVariants({ variant: "ghost", size: "sm" })}
                  >
                    Log in
                  </Link>
                  <Link
                    href="/register"
                    className={buttonVariants({ size: "sm" })}
                  >
                    Sign up
                  </Link>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </header>
  );
}
