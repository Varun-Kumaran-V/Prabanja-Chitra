/**
 * Page Layout wrapper component
 * Provides consistent structure across all pages
 */

import Navbar from './Navbar';
import Footer from './Footer';

export default function PageLayout({ 
  children, 
  showFooter = true,
  className = '',
  maxWidth = true,
}) {
  return (
    <div className="min-h-screen bg-[#10131a] text-[#e1e2eb] antialiased selection:bg-[#4fdbc8] selection:text-[#003731]">
      <Navbar />
      
      <main className={`pt-24 pb-12 ${maxWidth ? 'max-w-[1200px] mx-auto' : ''} ${className}`}>
        {children}
      </main>

      {showFooter && <Footer />}
    </div>
  );
}
