"use client";

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/navbar";
import { Spinner } from "@/components/ui/spinner";
import { ShieldX } from "lucide-react";

interface AdminLayoutProps {
  children: React.ReactNode;
}

export function AdminLayout({ children }: AdminLayoutProps) {
  const { isLoaded, isSignedIn, user } = useUser();
  const router = useRouter();

  // Still loading Clerk
  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  // Not signed in — redirect
  if (!isSignedIn) {
    router.replace("/sign-in");
    return null;
  }

  // Check role directly from publicMetadata — always accurate, no JWT parsing needed
  const role = user?.publicMetadata?.role as string | undefined;

  if (role !== "ADMIN") {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-background gap-4 text-center px-4">
        <div className="p-4 rounded-full bg-red-500/10">
          <ShieldX className="h-12 w-12 text-red-400" />
        </div>
        <h1 className="text-2xl font-bold">Access Denied</h1>
        <p className="text-muted-foreground max-w-sm">
          You don&apos;t have permission to access the admin panel. Please contact an administrator if you believe this is a mistake.
        </p>
        <button
          onClick={() => router.replace("/")}
          className="mt-2 px-5 py-2 rounded-lg bg-orange-500 hover:bg-orange-600 text-white font-medium transition-colors"
        >
          Go to Home
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar isAdmin={true} />
      <main className="flex-1 container mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
