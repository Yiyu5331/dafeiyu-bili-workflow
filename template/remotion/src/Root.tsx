import React from 'react';
import {Composition} from 'remotion';
import {Main as PhoneMain, FPS, TOTAL} from './Phone';

export const Root: React.FC = () => (
  <>
    <Composition id="PhoneUI" component={PhoneMain} durationInFrames={TOTAL} fps={FPS} width={1080} height={1920} />
  </>
);
