"use client";

import { Navbar } from "@/components/navbar";
import { useAuth, useUser } from "@clerk/nextjs";

interface CustomerLayoutProps {
  children: React.ReactNode;
}

export function CustomerLayout({ children }: CustomerLayoutProps) {
  const { isSignedIn } = useAuth();
  const { user } = useUser();

  const isAdmin = () => {
    if (!isSignedIn) return false;
    return user?.publicMetadata.role === "ADMIN";
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar isAdmin={isAdmin()} />
      <main className="flex-1">{children}</main>
      <footer className="border-t border-border/40 bg-card/50">
        <div className="container mx-auto px-4 py-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <h3 className="font-bold text-lg mb-4 text-foreground">LAK Hardware</h3>
              <p className="text-sm text-muted-foreground">Your trusted partner for quality chemicals, hardware, tools, and building materials.</p>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-foreground">Categories</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>Chemicals</li>
                <li>Tools</li>
                <li>Paints</li>
                <li>Electrical</li>
                <li>Plumbing</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-foreground">Quick Links</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>Products</li>
                <li>Request Quote</li>
                <li>Track Order</li>
                <li>Contact Us</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-foreground">Contact</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>No 10</li>
                <li>Dambulla Road, Naula</li>
                <li>+94 66 227 1017</li>
                <li>lakchemicalsandhardware@gmail.com</li>
              </ul>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-border/40 text-center text-sm text-muted-foreground">© 2026 LAK Chemicals and Hardware. All rights reserved.</div>
        </div>
      </footer>
    </div>
  );
}
