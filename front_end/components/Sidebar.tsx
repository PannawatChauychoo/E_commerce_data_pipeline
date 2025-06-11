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
      className={`flex items-center gap-3 px-3 py-3 text-md font-medium rounded-lg transition-colors
        ${isActive 
          ? 'bg-gray-100 text-primary dark:bg-gray-800' 
          : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-muted-foreground'
        }`}
    >
      <Icon className="w-5 h-5" />
      {label}
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
      label: 'Transactions',
      href: '/dashboard/transactions'
    },
    {
      icon: Activity,
      label: 'Monitoring',
      href: '/dashboard/monitoring'
    }
  ];

  return (
    <div className="w-50 border-r h-screen p-4">
      <nav className="space-y-2">
        {items.map((item) => (
          <SidebarItem key={item.href} {...item} />
        ))}
      </nav>
    </div>
  );
};

export default Sidebar; 