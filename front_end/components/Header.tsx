"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ThemeToggle } from './theme-toggle';
import { Download } from 'lucide-react';
import { Button } from './ui/button';

interface HeaderProps {
  onMenuClick?: () => void;
}

const Header = ({ onMenuClick }: HeaderProps) => {
  const pathname = usePathname();

  const navItems = [
    { name: 'Home', href: '/' },
    { name: 'Dashboard', href: '/dashboard/trends' },
    { name: 'Documentation', href: '/docs' },
  ];

  return (
    <header className="bg-card border-b border-border sticky top-0 z-50 w-full backdrop-blur-sm">
      <div className="container mx-auto px-6 h-16 flex items-center justify-between">
        <div className="text-lg font-bold">
          <a
            href="https://www.linkedin.com/in/pan2024/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-foreground hover:text-primary transition-colors duration-200 text-sm sm:text-base"
          >
            Walmart E-Commerce Simulation
            <span className="text-muted-foreground ml-2 hidden sm:inline">by Pannawat</span>
          </a>
        </div>
        <div className="flex items-center gap-2">
          <nav className="hidden md:block">
            <ul className="flex items-center space-x-1 gap-2">
              {navItems.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`px-3 py-1 rounded-md text-sm font-medium transition-all duration-200 hover:bg-accent hover:text-accent-foreground ${pathname === item.href
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground'
                      }`}
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
          <ThemeToggle />
          <Button
            variant="ghost"
            size="sm"
            onClick={onMenuClick}
            className="h-9 w-9 px-0"
          >
            <Download className="h-4 w-4" />
            <span className="sr-only">Download files</span>
          </Button>
          <div className="md:hidden">
            <button className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header; 
