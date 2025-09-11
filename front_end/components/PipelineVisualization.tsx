import React from 'react';
import Link from 'next/link';
import {
  Database,
  GitBranch,
  LineChart,
  Brain,
  ArrowRight,
  BarChart3,
  Sparkles
} from 'lucide-react';

const PipelineStep = ({
  icon: Icon,
  title,
  description,
  href
}: {
  icon: React.ElementType;
  title: string;
  description: string;
  href?: string;
}) => {
  const content = (
    <div className="bg-card border border-border rounded-xl p-6 text-center transition-all duration-300 hover:shadow-lg hover:shadow-primary/10 hover:-translate-y-1 flex flex-col items-center justify-between h-[225px] group">
      <div className="flex flex-col items-center flex-1 justify-center">
        <div className="bg-primary/10 p-4 rounded-2xl mb-4 group-hover:bg-primary/20 transition-colors">
          <Icon className="w-12 h-12 text-primary" />
        </div>
        <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
        <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
      </div>
      {href && (
        <div className="text-primary text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity mt-2">
          View Details →
        </div>
      )}
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="flex-1 min-w-0">
        {content}
      </Link>
    );
  }

  return (
    <div className="flex-1 min-w-0">
      {content}
    </div>
  );
};

const PipelineVisualization = () => {
  const steps = [
    {
      icon: Brain,
      title: "ABM Simulation",
      description: "Generate synthetic data"
    },
    {
      icon: Database,
      title: "PostgreSQL",
      description: "Store transaction data"
    },
    {
      icon: GitBranch,
      title: "ETL with DBT",
      description: "Transform and model data"
    },
    {
      icon: BarChart3,
      title: "Analytics",
      description: "Process and analyze data",
      href: "/dashboard/trends"
    },
  ];

  return (
    <div className="w-full">
      <div className="flex flex-col lg:flex-row items-center gap-6 lg:gap-2 xl:gap-4">
        {steps.map((step, index) => (
          <React.Fragment key={step.title}>
            <PipelineStep {...step} />
            {index < steps.length - 1 && (
              <ArrowRight className="w-8 h-8 lg:w-10 lg:h-10 xl:w-12 xl:h-12 text-primary rotate-90 lg:rotate-0 flex-shrink-0" />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default PipelineVisualization; 
