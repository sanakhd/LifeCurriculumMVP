import React, { useEffect, useRef, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { Menu, X, User, Settings, LogOut } from "lucide-react";
import "../styles/Navbar.css";

interface NavbarProps {
  userName: string;
  onLogout: () => void;
}

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/programs", label: "My Programs" },
  { to: "/progress", label: "Progress" },
];

export const Navbar: React.FC<NavbarProps> = ({ userName, onLogout }) => {
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const profileBtnRef = useRef<HTMLButtonElement>(null);
  const navigate = useNavigate();

  // Scroll shadow
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 6);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Outside click for dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!dropdownRef.current) return;
      const target = event.target as Node;
      if (!dropdownRef.current.contains(target) && target !== profileBtnRef.current) {
        setShowProfileMenu(false);
      }
    };
    if (showProfileMenu) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showProfileMenu]);

  // Keyboard close (Esc)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setShowProfileMenu(false);
        setMobileOpen(false);
        profileBtnRef.current?.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const handleLogout = () => {
    setShowProfileMenu(false);
    onLogout();
  };

  const initials = userName?.trim()?.[0]?.toUpperCase() || "U";

  return (
    <nav className={`navbar ${scrolled ? "navbar--scrolled" : ""}`} role="navigation" aria-label="Primary">
      <div className="navbar__inner">
        {/* Left: Logo */}
        <div className="logo-section" onClick={() => navigate("/dashboard")} role="button" tabIndex={0}
             onKeyDown={(e) => e.key === "Enter" && navigate("/dashboard")}>
          <div className="logo">
            <span className="logo-mark" aria-hidden />
            LifeCurriculum
          </div>
        </div>

        {/* Center: Links (desktop) */}
        <div className="nav-links" aria-label="Main">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            >
              <span className="nav-text">{item.label}</span>
              <span className="nav-underline" aria-hidden />
            </NavLink>
          ))}
        </div>

        {/* Right: Profile + Mobile Toggle */}
        <div className="right-side">
          <button
            ref={profileBtnRef}
            className="profile-avatar"
            onClick={() => setShowProfileMenu((s) => !s)}
            aria-haspopup="menu"
            aria-expanded={showProfileMenu}
            aria-controls="profile-menu"
          >
            {initials}
          </button>

          <button
            className="hamburger"
            aria-label={mobileOpen ? "Close menu" : "Open menu"}
            onClick={() => setMobileOpen((v) => !v)}
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          {showProfileMenu && (
            <div
              id="profile-menu"
              className="profile-dropdown"
              role="menu"
              ref={dropdownRef}
            >
              <div className="profile-info" role="none">
                <div className="profile-name">{userName}</div>
                <div className="profile-email">user@example.com</div>
              </div>
              <div className="profile-divider" role="none" />
              <button className="profile-menu-item" role="menuitem" onClick={() => { setShowProfileMenu(false); navigate("/profile"); }}>
                <User size={16} /> View Profile
              </button>
              <button className="profile-menu-item" role="menuitem" onClick={() => { setShowProfileMenu(false); navigate("/settings"); }}>
                <Settings size={16} /> Settings
              </button>
              <div className="profile-divider" role="none" />
              <button className="profile-menu-item logout" role="menuitem" onClick={handleLogout}>
                <LogOut size={16} /> Sign Out
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Mobile menu drawer (links) */}
      <div className={`mobile-drawer ${mobileOpen ? "open" : ""}`}>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `mobile-link ${isActive ? "active" : ""}`}
            onClick={() => setMobileOpen(false)}
          >
            {item.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
};