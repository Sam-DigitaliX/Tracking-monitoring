"use client";

import { Sidebar } from "@/components/layout/sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="ev-mesh-bg">
      <Sidebar />
      <main className="ml-[240px] min-h-screen transition-all duration-300">
        {children}
      </main>
    </div>
  );
}
