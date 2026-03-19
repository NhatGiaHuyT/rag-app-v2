"use client";

import { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Book,
  MessageSquare,
  LogOut,
  Menu,
  User,
  BarChart3,
  Shield,
  Briefcase,
} from "lucide-react";
import Breadcrumb from "@/components/ui/breadcrumb";
import { api } from "@/lib/api";

interface CurrentUser {
  username: string;
  full_name?: string | null;
  is_superuser: boolean;
  is_expert: boolean;
  role?: string;
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }
    api
      .get("/api/auth/me")
      .then(setCurrentUser)
      .catch(() => {
        localStorage.removeItem("token");
        router.push("/login");
      });
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  const navigation = [
    { name: "Knowledge Base", href: "/dashboard/knowledge", icon: Book },
    { name: "Chat", href: "/dashboard/chat", icon: MessageSquare },
    { name: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
    { name: "Profile", href: "/dashboard/profile", icon: User },
    { name: "API Keys", href: "/dashboard/api-keys", icon: Shield },
  ];

  if (currentUser?.is_superuser || currentUser?.role === "admin" || currentUser?.role === "super_admin") {
    navigation.splice(3, 0, {
      name: "Admin",
      href: "/dashboard/admin",
      icon: Shield,
    });
  }
  if (currentUser?.is_expert || currentUser?.role === "expert" || currentUser?.role === "super_admin") {
    navigation.splice(
      currentUser?.is_superuser || currentUser?.role === "admin" || currentUser?.role === "super_admin" ? 4 : 3,
      0,
      {
        name: "Expert Review",
        href: "/dashboard/expert-review",
        icon: Briefcase,
      }
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile menu button */}
      <div className="lg:hidden fixed top-0 left-0 m-4 z-50">
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 rounded-md bg-primary text-primary-foreground"
        >
          <Menu className="h-6 w-6" />
        </button>
      </div>

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-40 w-64 transform bg-card border-r transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-full flex-col">
          {/* Sidebar header */}
          <div className="flex h-16 items-center border-b pl-8">
            <Link
              href="/dashboard"
              className="flex items-center text-lg font-semibold hover:text-primary transition-colors"
            >
              <img
                src="/logo.svg"
                alt="Logo"
                className="w-16 h-16 rounded-lg"
              />
              RAG App
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-2 px-4 py-6">
            {navigation.map((item) => {
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`group flex items-center rounded-lg px-4 py-3 text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? "bg-gradient-to-r from-primary/10 to-primary/5 text-primary shadow-sm"
                      : "text-muted-foreground hover:bg-accent/50 hover:text-foreground hover:shadow-sm"
                  }`}
                >
                  <item.icon
                    className={`mr-3 h-5 w-5 transition-transform duration-200 ${
                      isActive
                        ? "text-primary scale-110"
                        : "group-hover:scale-110"
                    }`}
                  />
                  <span className="font-medium">{item.name}</span>
                  {isActive && (
                    <div className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
                  )}
                </Link>
              );
            })}
          </nav>
          {/* User profile and logout */}
          <div className="border-t p-4 space-y-4">
            {currentUser && (
              <div className="rounded-lg border bg-background/70 px-3 py-3">
                <p className="text-sm font-semibold">
                  {currentUser.full_name || currentUser.username}
                </p>
                <p className="text-xs text-muted-foreground">
                  {currentUser.is_superuser
                    ? "Super Admin"
                    : currentUser.role === "admin"
                    ? "Admin"
                    : currentUser.is_expert || currentUser.role === "expert"
                    ? "Expert reviewer"
                    : "User"}
                </p>
              </div>
            )}
            <button
              onClick={handleLogout}
              className="flex w-full items-center rounded-lg px-3 py-2.5 text-sm font-medium text-destructive hover:bg-destructive/10 transition-colors duration-200"
            >
              <LogOut className="mr-3 h-4 w-4" />
              Sign out
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        <main className="min-h-screen py-6 px-4 sm:px-6 lg:px-8">
          <Breadcrumb />
          {children}
        </main>
      </div>
    </div>
  );
}

export const dashboardConfig = {
  mainNav: [],
  sidebarNav: [
    {
      title: "Knowledge Base",
      href: "/dashboard/knowledge",
      icon: "database",
    },
    {
      title: "Chat",
      href: "/dashboard/chat",
      icon: "messageSquare",
    },
    {
      title: "API Keys",
      href: "/dashboard/api-keys",
      icon: "key",
    },
  ],
};
