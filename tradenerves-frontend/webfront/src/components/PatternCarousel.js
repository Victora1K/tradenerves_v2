// File: PatternCarousel.js

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import hammer from '../image-patterns/hammer.png';
import hangingman from '../image-patterns/hanging-man.png';
import threeblackcrows from '../image-patterns/three-black-crows.png';

const patternData = [
  { name: 'Hammer', imgSrc: hammer, link: '/patterns#hammer' },
  { name: 'Three Black Crows', imgSrc: threeblackcrows, link: '/patterns#threeblackcrows' },
  { name: 'Hanging Man', imgSrc: hangingman, link: '/patterns#hanging-man' },
  // Add more patterns here
];

const PatternCarousel = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  // Move to the next slide every 3 seconds if playing
  useEffect(() => {
    let interval;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentIndex((prevIndex) => (prevIndex + 1) % patternData.length);
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  const handlePrev = () => {
    setCurrentIndex((prevIndex) => (prevIndex === 0 ? patternData.length - 1 : prevIndex - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prevIndex) => (prevIndex + 1) % patternData.length);
  };

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  return (
    <div style={carouselContainerStyle}>
      <button onClick={handlePrev} style={{ ...navButtonStyle, left: '10px' }}>
        &#8249;
      </button>
      
      <div onClick={togglePlay} style={{ ...patternItemStyle, cursor: 'pointer' }}>
        <img 
          src={patternData[currentIndex].imgSrc} 
          alt={patternData[currentIndex].name} 
          style={imageStyle} 
        />
        <p>{patternData[currentIndex].name}</p>
        <p style={playStatusStyle}>{isPlaying ? 'Click to Pause' : 'Click to Play'}</p>
      </div>

      <button onClick={handleNext} style={{ ...navButtonStyle, right: '10px' }}>
        &#8250;
      </button>
    </div>
  );
};

const carouselContainerStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  position: 'relative',
  maxWidth: '70%',
  height: '400px',
  margin: '20px auto',
  overflow: 'hidden',
  backgroundColor: '#f5f5f5',
  borderRadius: '10px',
  boxShadow: '0 2px 5px rgba(0,0,0,0.1)',
};

const patternItemStyle = {
  textAlign: 'center',
  width: '100%',
  textDecoration: 'none',
  color: 'black',
  padding: '20px',
};

const imageStyle = {
  width: '90%',
  maxHeight: '250px',
  objectFit: 'contain',
  borderRadius: '8px',
  transition: 'transform 0.3s ease',
  '&:hover': {
    transform: 'scale(1.05)',
  },
};

const navButtonStyle = {
  position: 'absolute',
  top: '50%',
  transform: 'translateY(-50%)',
  backgroundColor: '#333',
  color: 'white',
  border: 'none',
  padding: '10px 15px',
  fontSize: '24px',
  cursor: 'pointer',
  zIndex: 1,
  borderRadius: '50%',
  opacity: 0.7,
  transition: 'opacity 0.3s ease',
  '&:hover': {
    opacity: 1,
  },
};

const playStatusStyle = {
  fontSize: '14px',
  color: '#666',
  marginTop: '5px',
};

export default PatternCarousel;
