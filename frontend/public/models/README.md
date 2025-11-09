# 3D Avatar Models Guide

This folder contains 3D avatar models for Juan and Sofia. The app will use stylized placeholders until you add custom models.

## How to Get FREE 3D Avatars

### Option 1: Ready Player Me (RECOMMENDED - Easiest)

**Best for:** Quick, professional, customizable avatars

1. Go to [https://readyplayer.me/](https://readyplayer.me/)
2. Click "Create Avatar"
3. Choose body type (male for Juan, female for Sofia)
4. Customize:
   - **Juan**: Dark hair, glasses, casual clothes
   - **Sofia**: Long hair, casual clothes, feminine style
5. Click "Export" → Download as GLB
6. Rename and place:
   - `juan.glb` for Juan
   - `sofia.glb` for Sofia

### Option 2: Sketchfab (FREE)

**Best for:** Pre-made characters with variety

1. Go to [https://sketchfab.com/3d-models](https://sketchfab.com/3d-models)
2. Search:
   - For Juan: "male character casual" or "businessman"
   - For Sofia: "female character casual" or "woman character"
3. Filter by:
   - ✅ Downloadable
   - ✅ Free
4. Download as GLB
5. Rename and place in this folder

### Option 3: Mixamo (FREE Adobe Account Required)

**Best for:** Rigged characters with animations

1. Go to [https://www.mixamo.com/](https://www.mixamo.com/)
2. Sign in with Adobe account (free)
3. Browse "Characters"
4. Select character and download as:
   - Format: GLB
   - Pose: T-pose
5. Rename and place in this folder

### Option 4: Custom Models

**Best for:** Full control and uniqueness

1. Use Blender (free) to create custom characters
2. Export as GLB format
3. Place in this folder

## File Structure

```
/public/models/
  ├── README.md (this file)
  ├── juan.glb (male avatar)
  └── sofia.glb (female avatar)
```

## Model Requirements

- **Format**: GLB (preferred) or GLTF
- **Size**: Under 10MB recommended
- **Optimization**: Use [glTF-Transform](https://gltf-transform.donmccurdy.com/) to optimize if needed
- **Orientation**: Characters should face forward (Z-axis)

## Quick Links

- [Ready Player Me](https://readyplayer.me/) - Generate custom avatars
- [Sketchfab](https://sketchfab.com/) - Download pre-made models
- [Mixamo](https://www.mixamo.com/) - Adobe's character library
- [glTF-Transform](https://gltf-transform.donmccurdy.com/) - Optimize GLB files

## Current Status

- **Juan**: Using stylized placeholder (blue theme)
- **Sofia**: Using stylized placeholder (pink theme)

Place your GLB files here to replace the placeholders!
