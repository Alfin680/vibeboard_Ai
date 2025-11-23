// import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// const isPublicRoute = createRouteMatcher([
//   "/",
//   "/signup",
// ]);

// export default clerkMiddleware(async (auth, req) => {
//   if (!isPublicRoute(req)) {
//     const { userId, redirectToSignIn } = await auth();

//     if (!userId) {
//       return redirectToSignIn();
//     }
//   }
// });

// export const config = {
//   matcher: [
//     "/((?!.*\\..*|_next).*)", 
//     "/", 
//     "/(api|trpc)(.*)"
//   ],
// };
// middleware.ts
// import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// const isPublicRoute = createRouteMatcher([
//   "/dashboard",
//   "/signup",
// ]);

// export default clerkMiddleware(async (auth, req) => {
//   if (!isPublicRoute(req)) {
//     const { userId, redirectToSignIn } = await auth();

//     if (!userId) {
//       return redirectToSignIn({ returnBackUrl: "/dashboard" });
//     }
//   }
// });

// export const config = {
//   matcher: [
//     "/((?!.*\\..*|_next).*)",
//     "/",
//     "/(api|trpc)(.*)",
//   ],
// };

import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/dashboard",
  "/signup",
  "/sso-callback",
]);

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) {
    const { userId, redirectToSignIn } = await auth();
    if (!userId) return redirectToSignIn();
  }
});

export const config = {
  matcher: [
    "/((?!.*\\..*|_next).*)",
    "/",
    "/(api|trpc)(.*)",
  ],
};
