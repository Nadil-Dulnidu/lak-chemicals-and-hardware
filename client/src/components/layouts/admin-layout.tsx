"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/navbar";
import { Spinner } from "@/components/ui/spinner";
import { ShieldX } from "lucide-react";

interface AdminLayoutProps {
  children: React.ReactNode;
}

function resolveRole(claims: Record<string, unknown> | null | undefined): string | null {
  if (!claims) return null;
  const direct = claims["role"];
  if (typeof direct === "string" && direct !== "") return direct;
  const pm = claims["public_metadata"];
  if (pm && typeof pm === "object") {
    const pmRole = (pm as Record<string, unknown>)["role"];
    if (typeof pmRole === "string" && pmRole !== "") return pmRole;
  }
  return null;
}

export function AdminLayout({ children }: AdminLayoutProps) {
  const { isLoaded, isSignedIn, sessionClaims } = useAuth();
  const router = useRouter();
  const [accessChecked, setAccessChecked] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    if (!isLoaded) return;

    if (!isSignedIn) {
      router.replace("/sign-in");
      return;
    }

    const role = resolveRole(sessionClaims as Record<string, unknown> | null);
    if (role === "ADMIN") {
      setIsAdmin(true);
    }
    setAccessChecked(true);
  }, [isLoaded, isSignedIn, sessionClaims, router]);

  // Still loading Clerk
  if (!isLoaded || !accessChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  // Signed in but not an admin
  if (!isAdmin) {
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
