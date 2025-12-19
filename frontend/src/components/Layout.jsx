import { useState, useEffect } from 'react';
import { Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import './Layout.css';

export default function Layout({ children, sidebar }) {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [isMobile, setIsMobile] = useState(false);

    // Check screen size
    useEffect(() => {
        const checkMobile = () => setIsMobile(window.innerWidth < 1024);
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    return (
        <div className="layout-container">
            {/* Desktop Sidebar */}
            {!isMobile && (
                <aside className="layout-sidebar desktop">
                    {sidebar}
                </aside>
            )}

            {/* Mobile Header */}
            {isMobile && (
                <header className="mobile-header glass-panel">
                    <div className="logo">🏛️ LLM Council</div>
                    <button
                        className="menu-btn"
                        onClick={() => setIsMobileMenuOpen(true)}
                    >
                        <Menu size={24} />
                    </button>
                </header>
            )}

            {/* Mobile Drawer */}
            <AnimatePresence>
                {isMobile && isMobileMenuOpen && (
                    <>
                        <motion.div
                            className="mobile-backdrop"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setIsMobileMenuOpen(false)}
                        />
                        <motion.aside
                            className="layout-sidebar mobile glass-panel"
                            initial={{ x: '-100%' }}
                            animate={{ x: 0 }}
                            exit={{ x: '-100%' }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                        >
                            <button
                                className="close-btn"
                                onClick={() => setIsMobileMenuOpen(false)}
                            >
                                <X size={24} />
                            </button>
                            {sidebar}
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>

            {/* Main Content */}
            <main className="layout-content">
                {children}
            </main>
        </div>
    );
}
