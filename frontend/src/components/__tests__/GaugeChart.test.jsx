import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import GaugeChart from '../GaugeChart';

describe('GaugeChart Component', () => {
  it('renders the gauge chart with the correct value', () => {
    render(<GaugeChart value={75} />);
    
    expect(screen.getByText('75')).toBeInTheDocument();
    expect(screen.getByText('Buy/Sell Ratio')).toBeInTheDocument();
  });

  it('displays low values (0-30)', () => {
    render(<GaugeChart value={20} />);
    
    expect(screen.getByText('20')).toBeInTheDocument();
  });

  it('displays medium values (31-70)', () => {
    render(<GaugeChart value={50} />);
    
    expect(screen.getByText('50')).toBeInTheDocument();
  });

  it('displays high values (71-100)', () => {
    render(<GaugeChart value={85} />);
    
    expect(screen.getByText('85')).toBeInTheDocument();
  });

  it('renders with value 0', () => {
    render(<GaugeChart value={0} />);
    
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('renders with value 100', () => {
    render(<GaugeChart value={100} />);
    
    expect(screen.getByText('100')).toBeInTheDocument();
  });
});
