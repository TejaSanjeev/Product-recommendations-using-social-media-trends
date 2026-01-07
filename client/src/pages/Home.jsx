import React from 'react';
import { Link } from 'react-router-dom';
import './Home.css';

const Home = () => {
  const categories = [
    { name: 'Electronics', path: '/category/electronics', icon: '📱' },
    { name: 'Services', path: '/category/services', icon: '🛠️' },
    { name: 'Tools', path: '/category/tools', icon: '🔧' },
    { name: 'Software', path: '/category/software', icon: '💻' },
    { name: 'Components', path: '/category/components', icon: '🧩' },
    { name: 'Development', path: '/category/development', icon: '⚙️' }
  ];

  // Items for animation
  const animatedItems = [
    { name: 'Smartphone Pro', icon: '📱', category: 'Electronics' },
    { name: 'Gaming Laptop', icon: '💻', category: 'Electronics' },
    { name: 'Wireless Speakers', icon: '🔊', category: 'Electronics' },
    { name: 'Running Shoes', icon: '👟', category: 'Fashion' },
    { name: 'Headphones', icon: '🎧', category: 'Electronics' },
    { name: 'Smart Watch', icon: '⌚', category: 'Electronics' },
    { name: 'Camera', icon: '📷', category: 'Electronics' },
    { name: 'Backpack', icon: '🎒', category: 'Fashion' },
    { name: 'Coffee Maker', icon: '☕', category: 'Appliances' },
    { name: 'Gaming Console', icon: '🎮', category: 'Electronics' },
    { name: 'Sunglasses', icon: '🕶️', category: 'Fashion' },
    { name: 'Tablet', icon: '📱', category: 'Electronics' },
    { name: 'Keyboard', icon: '⌨️', category: 'Electronics' },
    { name: 'Mouse', icon: '🖱️', category: 'Electronics' },
    { name: 'Sneakers', icon: '👟', category: 'Fashion' },
    { name: 'Desk Lamp', icon: '💡', category: 'Home' },
  ];

  return (
    <div className="home-page">
      <section className="hero-section">
        {/* Animated Items Background */}
        <div className="animated-items-container">
          {animatedItems.map((item, index) => (
            <div 
              key={index} 
              className={`floating-item floating-item-${index + 1}`}
              style={{ animationDelay: `${index * 0.5}s` }}
            >
              <span className="item-icon">{item.icon}</span>
              <span className="item-name">{item.name}</span>
            </div>
          ))}
        </div>
        
        {/* Hero Content */}
        <div className="hero-content">
          <h1 className="hero-title">Welcome to Item Gallery</h1>
          <p className="hero-subtitle">
            Explore our comprehensive collection of products and services across various categories.
            Click on any category below to discover amazing items tailored to your needs.
          </p>
        </div>
      </section>

      <section className="intro-section">
        <div className="intro-content">
          <h2>About Our Gallery</h2>
          <p>
            We provide a curated selection of high-quality items across multiple categories.
            Each item comes with detailed descriptions to help you make informed decisions.
          </p>
          <p>
            Browse by category to find exactly what you're looking for, or explore all items
            to discover something new.
          </p>
        </div>
      </section>

      <section className="categories-section">
        <h2 className="section-title">Explore Categories</h2>
        <div className="category-grid">
          {categories.map((category, index) => (
            <Link 
              key={index} 
              to={category.path} 
              className="category-card"
            >
              <span className="category-icon">{category.icon}</span>
              <h3 className="category-name">{category.name}</h3>
              <p className="category-cta">Browse items →</p>
            </Link>
          ))}
        </div>
      </section>

      <section className="features-section">
        <h2>Why Choose Us?</h2>
        <div className="features-grid">
          <div className="feature-item">
            <h3>🎯 Quality Selection</h3>
            <p>Carefully curated items across all categories</p>
          </div>
          <div className="feature-item">
            <h3>📋 Detailed Information</h3>
            <p>Comprehensive descriptions for every item</p>
          </div>
          <div className="feature-item">
            <h3>🚀 Easy Navigation</h3>
            <p>Intuitive interface for seamless browsing</p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;
