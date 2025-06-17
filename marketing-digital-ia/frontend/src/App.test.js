import { render, screen } from '@testing-library/react';
import AppWrapper from './App';

test('renders Radha One header', () => {
  render(<AppWrapper />);
  const headerElement = screen.getByRole('heading', { name: /radha one/i });
  expect(headerElement).toBeInTheDocument();
});
