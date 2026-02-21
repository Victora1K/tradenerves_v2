import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  BarChart3, 
  Calendar, 
  GraduationCap, 
  Menu, 
  X,
  Wallet
} from 'lucide-react';

const AppNavbar = ({ totalAccountValue }) => {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    { path: '/', label: 'Trade', icon: <TrendingUp size={18} /> },
    { path: '/patterns', label: 'Patterns', icon: <BarChart3 size={18} /> },
    { path: '/events', label: 'Events', icon: <Calendar size={18} /> },
    { path: '/practice', label: 'Practice', icon: <GraduationCap size={18} /> },
  ];

  const isActive = (path) => location.pathname === path;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value || 0);
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass-card border-b border-white/10">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center shadow-lg group-hover:shadow-primary-500/50 transition-all">
              <TrendingUp size={20} className="text-white" />
            </div>
            <span className="text-xl font-bold text-gradient">TradeNerves</span>
          </Link>

          {/* Desktop Navigation */}
          <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '0.25rem' }}>
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className="relative"
              >
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  style={{
                    display: 'flex',
                    flexDirection: 'row',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.5rem 1rem',
                    borderRadius: '0.5rem',
                    transition: 'all 0.2s',
                    backgroundColor: isActive(item.path) ? '#0284c7' : 'transparent',
                    color: isActive(item.path) ? '#ffffff' : '#d1d5db',
                    fontWeight: '500'
                  }}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </motion.div>
              </Link>
            ))}
          </div>

          {/* Account Value */}
          <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ 
              display: 'flex', 
              flexDirection: 'row', 
              alignItems: 'center', 
              gap: '0.5rem', 
              padding: '0.5rem 1rem', 
              borderRadius: '0.5rem', 
              border: '1px solid rgba(255, 255, 255, 0.1)', 
              backgroundColor: 'rgba(255, 255, 255, 0.05)' 
            }}>
              <Wallet size={18} style={{ color: '#38bdf8', flexShrink: 0 }} />
              <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ color: '#9ca3af', fontSize: '0.875rem' }}>Portfolio:</span>
                <span style={{ color: '#f3f4f6', fontSize: '0.875rem', fontWeight: '600' }}>
                  {formatCurrency(totalAccountValue)}
                </span>
              </div>
            </div>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 text-gray-300 hover:text-white hover:bg-white/5 rounded-lg transition-all"
          >
            {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden py-4 border-t border-white/10"
          >
            <div className="flex flex-col gap-2">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`
                    flex items-center gap-3 px-4 py-3 rounded-lg transition-all
                    ${isActive(item.path) 
                      ? 'bg-primary-600 text-white' 
                      : 'text-gray-300 hover:text-white hover:bg-white/5'
                    }
                  `}
                >
                  {item.icon}
                  <span className="font-medium">{item.label}</span>
                </Link>
              ))}
              <div className="mt-2 pt-2 border-t border-white/10">
                <div className="flex items-center gap-2 px-4 py-3 bg-white/5 rounded-lg">
                  <Wallet size={18} className="text-primary-400" />
                  <div className="flex flex-col">
                    <span className="text-xs text-gray-400">Portfolio Value</span>
                    <span className="text-sm font-semibold text-gray-100">
                      {formatCurrency(totalAccountValue)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </nav>
  );
};

export default AppNavbar;
