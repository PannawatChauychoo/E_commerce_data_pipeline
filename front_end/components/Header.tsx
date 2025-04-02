"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const Header = () => {
  const pathname = usePathname();

  const navItems = [
    { name: 'Home', href: '/' },
    { name: 'Dashboard', href: '/dashboard' },
    { name: 'Documentation', href: '/docs' },
  ];

  return (
    <header style={{ backgroundColor: '#3C3D37' }} className="shadow-md sticky top-0 z-50 w-full">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between text-white">
        <div className="text-xl font-bold text-white">
          <a 
            href="https://www.linkedin.com/in/pan2024/" 
            target="_blank" 
            rel="noopener noreferrer"
            className="hover:text-gray-300 transition-colors"
          >
            Pan AI
          </a>
        </div>
        <nav>
          <ul className="flex space-x-6">
            {navItems.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`text-md font-semibold transition-colors ${
                    pathname === item.href
                      ? 'text-white'
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  {item.name}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  );
};

export default Header; 