"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, FileText, Activity } from 'lucide-react';

const SidebarItem = ({
  icon: Icon,
  label,
  href
}: {
  icon: React.ElementType;
  label: string;
  href: string;
}) => {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link
      href={href}
      className={`flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200
        ${isActive
          ? 'bg-primary text-primary-foreground shadow-sm'
          : 'text-muted-foreground hover:text-foreground hover:bg-accent'
        }`}
    >
      <Icon className="w-5 h-5 shrink-0" />
      <span className="truncate">{label}</span>
    </Link>
  );
};

const Sidebar = () => {
  const items = [
    {
      icon: LayoutDashboard,
      label: 'Trends',
      href: '/dashboard/trends'
    },
    {
      icon: FileText,
      label: 'ML Analytics',
      href: '/dashboard/transactions'
    },
    {
      icon: Activity,
      label: 'Monitoring',
      href: '/dashboard/monitoring'
    }
  ];

  return (
    <div className="w-64 border-r border-border bg-card h-full p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-foreground mb-2">Dashboard</h2>
        <p className="text-sm text-muted-foreground">Analytics & Monitoring</p>
      </div>
      <nav className="space-y-1">
        {items.map((item) => (
          <SidebarItem key={item.href} {...item} />
        ))}
      </nav>
    </div>
  );
};

export default Sidebar; 
