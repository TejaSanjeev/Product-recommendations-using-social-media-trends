import React, { useState } from 'react';
import './ItemCard.css';

const ItemCard = ({ item }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleClick = (e) => {
    // Prevent expansion when clicking on the link
    if (e.target.tagName === 'A') {
      return;
    }
    setIsExpanded(!isExpanded);
  };

  const score = item.score || 0;

  return (
    <div className={`item-card ${isExpanded ? 'expanded' : ''}`} onClick={handleClick}>
      <div className="item-card-header">
        <h3 className="item-name">{item.name}</h3>
        <span className="toggle-icon">{isExpanded ? '−' : '+'}</span>
      </div>
      
      {/* Score Progress Bar */}
      <div className="item-score">
        <div className="score-label">
          <span>Score</span>
          <span className="score-value">{score}/100</span>
        </div>
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${score}%` }}
          ></div>
        </div>
      </div>

      {isExpanded && (
        <div className="item-description">
          <p>{item.description || item.summary || 'No description available.'}</p>
          {item.link && (
            <div className="item-link-container">
              <a 
                href={item.link} 
                target="_blank" 
                rel="noopener noreferrer"
                className="item-link"
                onClick={(e) => e.stopPropagation()}
              >
                View Details →
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ItemCard;
