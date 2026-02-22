import React from 'react';
import { motion } from 'framer-motion';

const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'md',
  icon,
  disabled = false,
  className = '',
  onClick,
  type = 'button',
  style = {},
  ...props 
}) => {
  const variantStyles = {
    primary: { backgroundColor: '#0ea5e9', color: '#ffffff', borderRadius: '0.5rem', fontWeight: '700', boxShadow: '0 0 12px rgba(14, 165, 233, 0.5)', border: '1px solid rgba(14,165,233,0.8)', transition: 'all 0.2s' },
    secondary: { backgroundColor: 'rgba(255,255,255,0.1)', color: '#f3f4f6', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '0.5rem', fontWeight: '500', transition: 'all 0.2s' },
    success: { backgroundColor: '#10b981', color: '#ffffff', borderRadius: '0.5rem', fontWeight: '500', transition: 'all 0.2s' },
    danger: { backgroundColor: '#ef4444', color: '#ffffff', borderRadius: '0.5rem', fontWeight: '500', transition: 'all 0.2s' },
    ghost: { backgroundColor: 'transparent', color: '#d1d5db', borderRadius: '0.5rem', transition: 'all 0.2s' },
    outline: { backgroundColor: 'transparent', color: '#38bdf8', border: '1px solid #38bdf8', borderRadius: '0.5rem', transition: 'all 0.2s' },
  };

  const sizes = {
    sm: 'text-xs px-3 py-1.5',
    md: 'text-sm px-4 py-2',
    lg: 'text-base px-6 py-3',
  };

  const disabledClasses = disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer';

  return (
    <motion.button
      whileHover={!disabled ? { scale: 1.02 } : {}}
      whileTap={!disabled ? { scale: 0.98 } : {}}
      className={`${sizes[size]} ${disabledClasses} ${className} flex items-center gap-2 justify-center`}
      style={{ ...variantStyles[variant], ...style }}
      onClick={onClick}
      disabled={disabled}
      type={type}
      {...props}
    >
      {icon && <span className="inline-flex">{icon}</span>}
      {children}
    </motion.button>
  );
};

export default Button;
