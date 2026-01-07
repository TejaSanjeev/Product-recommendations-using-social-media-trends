import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import ItemCard from '../components/ItemCard';
import './CategoryPage.css';

const CategoryPage = () => {
  const { categoryName } = useParams();
  const [items, setItems] = useState([]);

  useEffect(() => {
    // Simulate API call to fetch items by category
    // Replace this with actual API call: fetch(`/api/items?category=${categoryName}`)
    const mockApiData = [
      {
        id: 1,
        name: 'Product Alpha',
        description: 'This is a premium product with excellent features. It offers high performance and reliability for all your needs.',
        category: 'electronics',
        score: 92,
        link: 'https://example.com/product-alpha'
      },
      {
        id: 2,
        name: 'Service Beta',
        description: 'A comprehensive service solution designed to streamline your workflow and increase productivity.',
        category: 'services',
        score: 88,
        link: 'https://example.com/service-beta'
      },
      {
        id: 3,
        name: 'Tool Gamma',
        description: 'An innovative tool that simplifies complex tasks and saves time with its intuitive interface.',
        category: 'tools',
        score: 85,
        link: 'https://example.com/tool-gamma'
      },
      {
        id: 4,
        name: 'Platform Delta',
        description: 'A robust platform for managing all your business operations in one centralized location.',
        category: 'software',
        score: 95,
        link: 'https://example.com/platform-delta'
      },
      {
        id: 5,
        name: 'Module Epsilon',
        description: 'A modular solution that can be customized to fit your specific requirements and scale with your growth.',
        category: 'components',
        score: 78,
        link: 'https://example.com/module-epsilon'
      },
      {
        id: 6,
        name: 'Framework Zeta',
        description: 'A modern framework built with best practices to help you develop applications faster and more efficiently.',
        category: 'development',
        score: 91,
        link: 'https://example.com/framework-zeta'
      },
      {
        id: 7,
        name: 'Application Eta',
        description: 'A versatile application suitable for various use cases, from small projects to enterprise solutions.',
        category: 'software',
        score: 82,
        link: 'https://example.com/application-eta'
      },
      {
        id: 8,
        name: 'Widget Theta',
        description: 'A smart widget that enhances user experience with real-time updates and interactive features.',
        category: 'components',
        score: 89,
        link: 'https://example.com/widget-theta'
      },
      {
        id: 9,
        name: 'Smartphone Pro',
        description: 'Latest generation smartphone with advanced AI capabilities and stunning display technology.',
        category: 'electronics',
        score: 94,
        link: 'https://example.com/smartphone-pro'
      },
      {
        id: 10,
        name: 'Consulting Service',
        description: 'Professional consulting services to help your business grow and overcome challenges.',
        category: 'services',
        score: 86,
        link: 'https://example.com/consulting-service'
      },
      {
        id: 11,
        name: 'Power Drill X1',
        description: 'Heavy-duty power drill with multiple speed settings and long-lasting battery.',
        category: 'tools',
        score: 90,
        link: 'https://example.com/power-drill-x1'
      },
      {
        id: 12,
        name: 'Design Suite',
        description: 'Complete design software suite for professionals and creative enthusiasts.',
        category: 'software',
        score: 87,
        link: 'https://example.com/design-suite'
      }
    ];

    // Filter items by category
    const filteredItems = mockApiData.filter(
      item => item.category.toLowerCase() === categoryName.toLowerCase()
    );

    // Simulate API delay
    setTimeout(() => {
      setItems(filteredItems);
    }, 300);
  }, [categoryName]);

  const categoryDisplay = categoryName.charAt(0).toUpperCase() + categoryName.slice(1);

  return (
    <div className="category-page">
      <div className="category-header">
        <Link to="/" className="back-link">← Back to Home</Link>
        <h1 className="category-title">{categoryDisplay}</h1>
        <p className="category-description">
          Browse all items in the {categoryDisplay} category
        </p>
      </div>

      <div className="items-grid">
        {items.length === 0 ? (
          <div className="no-items">
            <p>No items found in this category.</p>
            <Link to="/" className="home-link">Return to Home</Link>
          </div>
        ) : (
          items.map(item => (
            <ItemCard key={item.id} item={item} />
          ))
        )}
      </div>
    </div>
  );
};

export default CategoryPage;
