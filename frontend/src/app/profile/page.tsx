"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { Loader2, User, KeyRound, ArrowLeft } from "lucide-react";

export default function ProfilePage() {
  const { user, updateUser, isLoading } = useAuth();

  const [fullName, setFullName] = useState("");
  const [bio, setBio] = useState("");
  const [avatar, setAvatar] = useState("");
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || "");
      setBio(user.bio || "");
      setAvatar(user.avatar || "");
    }
  }, [user]);

  if (isLoading) {
    return (
      <div className="container max-w-2xl mx-auto px-4 py-16 text-center">
        <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="container max-w-md mx-auto px-4 py-16 text-center space-y-4">
        <h2 className="text-2xl font-bold">Please Log In</h2>
        <p className="text-muted-foreground text-sm">You must be logged in to view and edit your profile.</p>
        <Button asChild>
          <Link href="/login">Log in</Link>
        </Button>
      </div>
    );
  }

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUpdatingProfile(true);

    try {
      const updated = await api.updateMe({
        full_name: fullName.trim() || undefined,
        bio: bio.trim() || undefined,
        avatar: avatar.trim() || undefined,
      });
      updateUser(updated);
      toast.success("Profile updated successfully!");
    } catch (err: any) {
      toast.error(err.message || "Failed to update profile");
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 6) {
      toast.error("New password must be at least 6 characters");
      return;
    }

    setIsChangingPassword(true);
    try {
      await api.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      toast.success("Password changed successfully!");
      setCurrentPassword("");
      setNewPassword("");
    } catch (err: any) {
      toast.error(err.message || "Failed to change password");
    } finally {
      setIsChangingPassword(false);
    }
  };

  const initials = user.full_name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="container max-w-3xl mx-auto px-4 py-10 space-y-8">
      <Button asChild variant="ghost" size="sm" className="gap-2 text-muted-foreground">
        <Link href="/">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to articles</span>
        </Link>
      </Button>

      {/* Profile Overview Card */}
      <Card className="border-border/60">
        <CardHeader>
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16 ring-2 ring-primary/20">
              <AvatarImage src={avatar || ""} alt={user.full_name} />
              <AvatarFallback className="text-lg">{initials}</AvatarFallback>
            </Avatar>
            <div>
              <CardTitle className="text-2xl font-bold">{user.full_name}</CardTitle>
              <CardDescription>@{user.username} • {user.email}</CardDescription>
            </div>
          </div>
        </CardHeader>

        <form onSubmit={handleUpdateProfile}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="fullName" className="text-sm font-medium">
                Full Name
              </label>
              <Input
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                disabled={isUpdatingProfile}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="avatar" className="text-sm font-medium">
                Avatar Image URL
              </label>
              <Input
                id="avatar"
                type="url"
                placeholder="https://example.com/avatar.jpg"
                value={avatar}
                onChange={(e) => setAvatar(e.target.value)}
                disabled={isUpdatingProfile}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="bio" className="text-sm font-medium">
                Bio
              </label>
              <Textarea
                id="bio"
                placeholder="Tell readers about yourself..."
                rows={3}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                disabled={isUpdatingProfile}
              />
            </div>

            <div className="flex justify-end pt-2">
              <Button type="submit" disabled={isUpdatingProfile}>
                {isUpdatingProfile ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  "Save Profile"
                )}
              </Button>
            </div>
          </CardContent>
        </form>
      </Card>

      {/* Change Password Card */}
      <Card className="border-border/60">
        <CardHeader>
          <div className="flex items-center gap-2 text-primary font-semibold text-sm mb-1">
            <KeyRound className="h-4 w-4" />
            <span>Security</span>
          </div>
          <CardTitle className="text-xl font-bold">Change Password</CardTitle>
          <CardDescription>Ensure your account remains secure with a strong password.</CardDescription>
        </CardHeader>

        <form onSubmit={handleChangePassword}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="currentPassword" className="text-sm font-medium">
                Current Password
              </label>
              <Input
                id="currentPassword"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                disabled={isChangingPassword}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="newPassword" className="text-sm font-medium">
                New Password
              </label>
              <Input
                id="newPassword"
                type="password"
                placeholder="At least 6 characters"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                disabled={isChangingPassword}
              />
            </div>

            <div className="flex justify-end pt-2">
              <Button type="submit" variant="outline" disabled={isChangingPassword}>
                {isChangingPassword ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Updating...
                  </>
                ) : (
                  "Update Password"
                )}
              </Button>
            </div>
          </CardContent>
        </form>
      </Card>
    </div>
  );
}
