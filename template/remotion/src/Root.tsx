import React from 'react';
import {Composition} from 'remotion';
import {Main as PhoneMain, FPS, TOTAL} from './Phone';
import {Reveal, REVEAL_TOTAL} from './Reveal';

export const Root: React.FC = () => (
  <>
    <Composition id="PhoneUI" component={PhoneMain} durationInFrames={TOTAL} fps={FPS} width={1080} height={1920} />
    <Composition id="Reveal" component={Reveal} durationInFrames={REVEAL_TOTAL()} fps={FPS} width={1080} height={1920} />
  </>
);
