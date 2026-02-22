// File: PatternsInfo.js

import React from 'react';
import hammer from '../image-patterns/hammer.png';
import hangingman from '../image-patterns/hanging-man.png';
import threeblackcrows from '../image-patterns/three-black-crows.png';
import Card from './ui/Card';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Info } from 'lucide-react';

const patternsInfoData = [
    {
      name: 'Hammer',
      type: 'Bullish Reversal',
      description: 'The hammer candlestick pattern is a bullish reversal pattern that forms at the bottom of a downtrend. It signals potential upward momentum with a small body and long lower shadow, indicating buyers stepped in to push prices higher.',
      imgSrc: hammer,
      signal: 'bullish',
    },
    {
      name: 'Three Black Crows',
      type: 'Bearish Reversal',
      description: 'The three black crows is a bearish reversal pattern consisting of three consecutive long red candles with lower closes. This pattern suggests strong selling pressure and potential continuation of a downtrend.',
      imgSrc: threeblackcrows,
      signal: 'bearish',
    },
    {
      name: 'Hanging Man',
      type: 'Bearish Reversal',
      description: 'The hanging man is a bearish reversal pattern typically seen at the top of an uptrend. Similar in appearance to a hammer but occurring after a rally, it signals potential reversal as sellers begin to overwhelm buyers.',
      imgSrc: hangingman,
      signal: 'bearish',
    },
  ];

const PatternsInfo = () => {
    return (
        <div className="container mx-auto px-4 py-6 space-y-6">
            {/* Header */}
            <motion.div 
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <h1 className="text-3xl font-bold text-gradient mb-2">Candlestick Patterns</h1>
                <p className="text-gray-400 text-sm">
                    Learn about key technical analysis patterns used in trading
                </p>
            </motion.div>

            {/* Info Banner */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="glass-card p-4 border-primary-500/30"
            >
                <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-primary-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                        <Info className="text-primary-400" size={20} />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-gray-100 mb-1">Pattern Recognition</h3>
                        <p className="text-sm text-gray-400">
                            These patterns are identified automatically in our trading dashboard. Understanding them helps you make better trading decisions.
                        </p>
                    </div>
                </div>
            </motion.div>

            {/* Patterns Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {patternsInfoData.map((pattern, index) => (
                    <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 * (index + 1) }}
                    >
                        <Card hover className="h-full">
                            {/* Pattern Image */}
                            <div className="mb-4 p-4 bg-white/5 rounded-lg flex justify-center">
                                <img 
                                    src={pattern.imgSrc} 
                                    alt={pattern.name} 
                                    className="h-32 md:h-48 w-auto max-w-full object-contain"
                                />
                            </div>

                            {/* Pattern Info */}
                            <div className="space-y-3">
                                <div>
                                    <h3 className="text-xl font-bold text-gray-100 mb-1">{pattern.name}</h3>
                                    <div className="flex items-center gap-2">
                                        {pattern.signal === 'bullish' ? (
                                            <div className="flex items-center gap-1 px-2 py-1 bg-green-500/20 rounded text-green-400 text-xs font-medium">
                                                <TrendingUp size={14} />
                                                {pattern.type}
                                            </div>
                                        ) : (
                                            <div className="flex items-center gap-1 px-2 py-1 bg-red-500/20 rounded text-red-400 text-xs font-medium">
                                                <TrendingDown size={14} />
                                                {pattern.type}
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <p className="text-sm text-gray-400 leading-relaxed">
                                    {pattern.description}
                                </p>
                            </div>
                        </Card>
                    </motion.div>
                ))}
            </div>

            {/* Coming Soon Card */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
            >
                <Card className="text-center">
                    <div className="py-8">
                        <h3 className="text-xl font-semibold text-gray-100 mb-2">More Patterns Coming Soon</h3>
                        <p className="text-gray-400 text-sm mb-4">
                            We're continuously adding more candlestick patterns including Doji, Engulfing, and Morning Star.
                        </p>
                        <a 
                            href='https://a.webull.com/NwcK53BxT9BKOwjEn5'
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-primary inline-block"
                        >
                            Start Trading on Webull
                        </a>
                    </div>
                </Card>
            </motion.div>
        </div>
    );
};

export default PatternsInfo;