import { Components, Theme } from '@mui/material/styles';
import { buttonOverrides } from './button';
import { paperOverrides } from './card';

export const componentsOverrides: Components<Theme> = {
  MuiButton: buttonOverrides,
  MuiPaper: paperOverrides,
};
