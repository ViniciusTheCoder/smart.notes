"use client";

import React from 'react';
import { LucideIcon } from 'lucide-react';

interface FeatureCardProps {
  title: string;
  description: string;
  icon: LucideIcon; 
}

const FeatureCard: React.FC<FeatureCardProps> = ({ title, description, icon: Icon }) => (
  <div className="group p-6 sm:p-8 rounded-2xl bg-white/5 hover:bg-white/10 backdrop-blur-sm transition-all duration-300 hover:scale-105">
    <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center mb-4 group-hover:bg-purple-500/30 transition-colors">
      <Icon className="w-6 h-6 text-purple-400" />
    </div>
    <h3 className="text-lg sm:text-xl font-semibold mb-2">{title}</h3>
    <p className="text-sm sm:text-base text-gray-700">{description}</p>
  </div>
);

export default FeatureCard;
