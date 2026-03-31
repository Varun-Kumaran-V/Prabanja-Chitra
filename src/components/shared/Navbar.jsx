import { Link, useLocation } from 'react-router-dom';

const navLinks = [
  { path: '/home', label: 'Home' },
  { path: '/mission-control', label: 'Mission Control' },
  { path: '/comparison', label: 'Comparison' },
  { path: '/metrics', label: 'Metrics' },
  { path: '/architecture', label: 'Architecture' },
];

export default function Navbar() {
  const location = useLocation();
  const currentPath = location.pathname;

  return (
    <nav className="fixed top-0 w-full z-50 bg-[#1d2026]/80 backdrop-blur-xl border-b border-[#4fdbc8]/15 shadow-[0_24px_48px_rgba(0,0,0,0.4)]">
      <div className="flex justify-between items-center h-16 px-6 md:px-8 max-w-[1440px] mx-auto">
        {/* Logo */}
        <Link 
          to="/home" 
          className="text-xl font-semibold tracking-[-0.02em] text-[#e1e2eb] hover:text-[#4fdbc8] transition-colors"
        >
          Prabanja Chitra
        </Link>

        {/* Nav Links - Desktop */}
        <div className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => {
            const isActive = currentPath === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`
                  px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                  ${isActive 
                    ? 'text-[#4fdbc8] bg-[#4fdbc8]/10' 
                    : 'text-[#e1e2eb]/70 hover:text-[#e1e2eb] hover:bg-[#272a31]'
                  }
                `}
              >
                {link.label}
              </Link>
            );
          })}
        </div>

        {/* CTA Button */}
        <Link
          to="/dashboard"
          className="
            bg-[#4fdbc8] text-[#003731] px-5 py-2.5 rounded-xl text-sm font-semibold
            hover:bg-[#3cc9b5] active:scale-95 transition-all duration-150
            shadow-[0_0_20px_rgba(79,219,200,0.25)] hover:shadow-[0_0_30px_rgba(79,219,200,0.4)]
          "
        >
          Launch Dashboard
        </Link>

        {/* Mobile Menu Button */}
        <button className="md:hidden text-[#e1e2eb] p-2 hover:bg-[#272a31] rounded-lg transition-colors">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>
    </nav>
  );
}
