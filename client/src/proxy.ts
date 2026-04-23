import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

const isProtectedRoute = createRouteMatcher([
  "/cart(.*)",
  "/quotations(.*)",
  "/orders(.*)",
  "/admin(.*)",
  "/chat(.*)",
]);

const isAdminRoute = createRouteMatcher(["/admin(.*)"]);

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

export default clerkMiddleware(async (auth, request) => {
  if (isProtectedRoute(request)) {
    // Ensure user is signed in first
    await auth.protect();
  }

  if (isAdminRoute(request)) {
    const { sessionClaims } = await auth();
    const role = resolveRole(sessionClaims as Record<string, unknown> | null);

    if (role !== "ADMIN") {
      // Redirect non-admins to the home page
      const homeUrl = new URL("/", request.url);
      return NextResponse.redirect(homeUrl);
    }
  }
});

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
};
