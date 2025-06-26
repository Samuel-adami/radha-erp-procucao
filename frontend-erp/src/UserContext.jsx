import React from 'react';

export const UserContext = React.createContext(null);

export function useUsuario() {
  return React.useContext(UserContext);
}
