import { clerkMiddleware, createRouteMatcher, createClerkClient } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

const isProtectedRoute = createRouteMatcher([
  "/cart(.*)",
  "/quotations(.*)",
  "/orders(.*)",
  "/admin(.*)",
  "/chat(.*)",
]);

const isAdminRoute = createRouteMatcher(["/admin(.*)"]);

/**
 * Extract the role from Clerk session claims.
 * Checks two locations:
 * 1. Top-level `role` claim  (set by the custom JWT template "lak-chemicles-and-hardware")
 * 2. `public_metadata.role`  (set in Clerk Dashboard → User → Public Metadata)
 */
function resolveRoleFromClaims(claims: Record<string, unknown> | null | undefined): string | null {
  if (!claims) return null;
  // 1. Top-level from custom JWT template
  const direct = claims["role"];
  if (typeof direct === "string" && direct !== "") return direct;
  // 2. publicMetadata embedded in default session token
  const pm = claims["public_metadata"];
  if (pm && typeof pm === "object") {
    const pmRole = (pm as Record<string, unknown>)["role"];
    if (typeof pmRole === "string" && pmRole !== "") return pmRole;
  }
  return null;
}

export default clerkMiddleware(async (auth, request) => {
  // Step 1: require sign-in for all protected routes
  if (isProtectedRoute(request)) {
    await auth.protect();
  }

  // Step 2: require ADMIN role for all /admin/* routes
  if (isAdminRoute(request)) {
    const { userId, sessionClaims } = await auth();

    // Fast path: read role from session claims
    let role = resolveRoleFromClaims(sessionClaims as Record<string, unknown> | null);

    // Fallback: fetch directly from Clerk Backend API if not in claims
    if (!role && userId) {
      try {
        const clerk = createClerkClient({ secretKey: process.env.CLERK_SECRET_KEY });
        const user = await clerk.users.getUser(userId);
        const metadata = user.publicMetadata as Record<string, unknown>;
        role = (metadata?.role as string) ?? null;
      } catch {
        role = null;
      }
    }

    if (role !== "ADMIN") {
      return NextResponse.redirect(new URL("/", request.url));
    }
  }
});

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
};
