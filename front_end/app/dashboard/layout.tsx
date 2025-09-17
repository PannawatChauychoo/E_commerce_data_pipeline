"use client";

import { useState } from 'react';
import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';
import { FileSidebar } from '@/components/FileSidebar';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isFileSidebarOpen, setIsFileSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <Header onMenuClick={() => setIsFileSidebarOpen(true)} />
      <div className="flex h-[calc(100vh-64px)]">
        <Sidebar />
        <main className="flex-1 overflow-auto bg-background">
          <div className="p-8">
            <div className="max-w-7xl mx-auto">
              {children}
            </div>
          </div>
        </main>
      </div>
      <FileSidebar
        isOpen={isFileSidebarOpen}
        onClose={() => setIsFileSidebarOpen(false)}
      />
    </div>
  );
} 
