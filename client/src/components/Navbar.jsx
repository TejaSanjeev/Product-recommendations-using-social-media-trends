import React from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

const Navbar = () => {
  const categories = [
    { name: 'Electronics', path: '/category/electronics' },
    { name: 'Services', path: '/category/services' },
    { name: 'Tools', path: '/category/tools' },
    { name: 'Software', path: '/category/software' },
    { name: 'Components', path: '/category/components' },
    { name: 'Development', path: '/category/development' }
  ];

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-title">TREND-ITEM</Link>
        <ul className="navbar-categories">
          {categories.map((category, index) => (
            <li key={index} className="navbar-category">
              <Link to={category.path} className="navbar-link">
                {category.name}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
};

export default Navbar;
