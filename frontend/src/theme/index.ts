import { createTheme } from '@mui/material/styles';
import { palette } from './palette';
import { typography } from './typography';
import { componentsOverrides } from './components';

export const appTheme = createTheme({
  palette,
  typography,
  shape: {
    borderRadius: 10,
  },
  components: componentsOverrides,
});

export default appTheme;
