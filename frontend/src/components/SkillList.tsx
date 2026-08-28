import React from 'react';
import { useStore } from '../hooks/useStore';
import type { Skill } from '../types';

export function SkillList() {
  const { skills, fetchSkills } = useStore();

  React.useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  if (skills.length === 0) return null;

  return (
    <div className="space-y-1.5">
      <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest px-1">Skills</h3>
      {skills.map((skill) => (
        <SkillItem key={skill.name} skill={skill} />
      ))}
    </div>
  );
}

function SkillItem({ skill }: { skill: Skill }) {
  return (
    <div className="px-3 py-2 bg-gray-800/50 rounded-lg border border-gray-800 hover:border-gray-700 transition-colors">
      <p className="text-xs font-medium text-gray-300 capitalize">{skill.name}</p>
      <p className="text-[10px] text-gray-500 mt-0.5 line-clamp-1">{skill.description}</p>
    </div>
  );
}
