"use client";

import { Navbar } from "@/components/navbar";

interface AdminLayoutProps {
  children: React.ReactNode;
}

export function AdminLayout({ children }: AdminLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar isAdmin={true} />
      <main className="flex-1 container mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
