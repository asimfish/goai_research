"""Hero renders of layout v4 for the promotional cover (docs/competition/cover, 2026-09-18).
Explored and rejected: corner_mid/corner_low/shoulder/rail_hero/c_to_b/b_corner, A_low/C_high/mid_room/B_hero2, C_low/C_low2/A_low2.
The GI pass looked identical to the accepted real-time look; the path-tracing pass ran out of GPU memory at 7 x 3000x2000 and was dropped.
Hero renders of layout v4 for the promotional cover: closer, lower, wider cameras than the fixed overview,
all six doors open, high resolution (default 3000x2000). Three passes per camera so the author can pick a look:
  rt  = the accepted look of the existing renders (RTX real-time, no GI)
  gi  = same, with indirect diffuse (global illumination) on
  pt  = path tracing (accumulated spp, denoised)

Run from the v4render dir:  bash launch.sh hero_render.py [--width 3000 --height 2000] [--only name,name]
Writes hero/hero_<camera>_<pass>.png and hero/hero_report.json. Nothing else in v4render is touched.
"""
import argparse, json, time, traceback
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'hero'
OUT.mkdir(exist_ok=True)
START = time.time()
from isaaclab.app import AppLauncher

ap = argparse.ArgumentParser()
ap.add_argument('--width', type=int, default=3000)
ap.add_argument('--height', type=int, default=2000)
ap.add_argument('--only', type=str, default='')
ap.add_argument('--passes', type=str, default='rt')
ap.add_argument('--pt-rounds', type=int, default=48)
ap.add_argument('--pt-spp', type=int, default=4)
AppLauncher.add_app_launcher_args(ap)
args = ap.parse_args()
app = AppLauncher(args).app

# name, eye, target, focal (mm on a 24 mm horizontal aperture). Room verified extent x -4.5..4.0, y -3.2..3.0, ceiling 3.34.
HERO = [
    # A 版：配料站一角推近的全景（overview_1 同一方向，推近、放低、加广角，稍向下俯）
    ('A_close', [3.5, 1.3, 2.3],  [-1.0, -2.0, 0.45], 13.0),
    # B 版：XRD 站一角的反向全景（沿 -x 看过 C 站与配料岛，远端是马弗炉阵列与导轨 UR5e）
    ('C_high2', [3.9, -1.6, 2.7], [-1.8, -0.2, 0.7],  13.0),
]
if args.only:
    keep = set(args.only.split(','))
    HERO = [h for h in HERO if h[0] in keep]
passes = [p for p in args.passes.split(',') if p]

report = {'width': args.width, 'height': args.height, 'cameras': {n: {'eye': e, 'target': t, 'focal': f} for n, e, t, f in HERO},
          'passes': {}, 'doors': {}}
try:
    import numpy as np
    from PIL import Image
    import carb
    import isaaclab.sim as sim_utils
    from isaaclab.scene import InteractiveScene
    from isaaclab.sensors import CameraCfg
    import scene_cfg_twin as S
    from scene_cfg_twin import PLAN

    def hero_camera(path, eye, target, focal=16.):
        return CameraCfg(prim_path=path, width=args.width, height=args.height, update_period=0., data_types=['rgb'],
                         spawn=sim_utils.PinholeCameraCfg(focal_length=focal, horizontal_aperture=24., clipping_range=(.05, 40.)),
                         offset=CameraCfg.OffsetCfg(pos=tuple(eye), rot=S.camera_quat(eye, target), convention='world'))

    S.camera = hero_camera
    PLAN['cameras'] = [{'name': n, 'eye': e, 'target': t, 'focal': f} for n, e, t, f in HERO]
    from scene_cfg_twin import GOAI_SCENE_CFG

    render = sim_utils.RenderCfg(enable_translucency=True, enable_reflections=True, enable_global_illumination=False,
                                 antialiasing_mode='TAA', enable_dlssg=False, enable_dl_denoiser=False,
                                 samples_per_pixel=1, enable_shadows=True, enable_ambient_occlusion=True)
    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=1 / 60, device='cpu', use_fabric=True, render=render,
        physx=sim_utils.PhysxCfg(solver_type=1, max_position_iteration_count=16, max_velocity_iteration_count=2, enable_ccd=True)))
    settings = carb.settings.get_settings()
    settings.set_bool('/physics/fabricUpdateTransformations', True)
    scene = InteractiveScene(GOAI_SCENE_CFG(num_envs=1, env_spacing=2.))
    sim.reset()
    for r in PLAN['robots']:
        rb = scene[r['prim_path'].split('/')[-1]]
        rb.write_joint_state_to_sim(rb.data.default_joint_pos, rb.data.default_joint_vel)
        rb.set_joint_position_target(rb.data.default_joint_pos)
    arts = {}
    for p in PLAN['prims']:
        if p.get('articulated'):
            a = scene[p['name']]
            a.write_joint_state_to_sim(a.data.default_joint_pos, a.data.default_joint_vel)
            a.set_joint_position_target(a.data.default_joint_pos)
            arts[p['name']] = a
    scene.reset()
    for i in range(90):
        scene.write_data_to_sim(); sim.step(render=(i % 10 == 0)); scene.update(1 / 60)

    # all six doors open (furnaces + drying oven 1.5 rad, XRD window slide 0.4795 m), as in the accepted open_* renders
    for p in PLAN['prims']:
        if not p.get('articulated'):
            continue
        a = arts[p['name']]
        jn = p.get('joint_name')
        idx = a.joint_names.index(jn) if jn in a.joint_names else 0
        target = float(p.get('open_target_rad') or 1.5) if jn else 0.4795
        tgt = a.data.default_joint_pos.clone()
        tgt[0, idx] = target
        a.set_joint_position_target(tgt)
        report['doors'][p['name']] = {'joint': jn or a.joint_names[idx], 'target': target}
    for i in range(300):
        scene.write_data_to_sim(); sim.step(render=(i % 15 == 0)); scene.update(1 / 60)
    for p in PLAN['prims']:
        if p.get('articulated'):
            a = arts[p['name']]
            jn = p.get('joint_name'); idx = a.joint_names.index(jn) if jn in a.joint_names else 0
            report['doors'][p['name']]['reached'] = round(float(a.data.joint_pos[0, idx]), 4)
    print('DOORS', json.dumps(report['doors']), flush=True)

    def shoot(tag, warm):
        for _ in range(warm):
            sim.render()
        res = {}
        for cam in PLAN['cameras']:
            c = scene[f"{cam['name']}_camera"]; c.update(1 / 60, force_recompute=True)
            rgb = c.data.output['rgb'][0, ..., :3].cpu().numpy()
            Image.fromarray(rgb).save(OUT / f"hero_{cam['name']}_{tag}.png")
            res[cam['name']] = {'mean': round(float(rgb.mean()), 1), 'std': round(float(rgb.std()), 1), 'ok': bool(rgb.std() > 5)}
        report['passes'][tag] = {'shots': res, 't_s': round(time.time() - START, 1)}
        (OUT / 'hero_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
        print('PASS', tag, json.dumps(res), flush=True)

    if 'rt' in passes:
        shoot('rt', 40)
    if 'gi' in passes:
        try:
            settings.set_bool('/rtx/indirectDiffuse/enabled', True)
            shoot('gi', 48)
        except Exception:
            report['passes']['gi'] = {'error': traceback.format_exc()[-800:]}
    if 'pt' in passes:
        try:
            settings.set_string('/rtx/rendermode', 'PathTracing')
            settings.set_int('/rtx/pathtracing/spp', args.pt_spp)
            settings.set_int('/rtx/pathtracing/totalSpp', args.pt_rounds * args.pt_spp)
            settings.set_int('/rtx/pathtracing/maxBounces', 6)
            settings.set_int('/rtx/pathtracing/maxSpecularAndTransmissionBounces', 8)
            settings.set_bool('/rtx/pathtracing/optixDenoiser/enabled', True)
            settings.set_bool('/rtx/pathtracing/denoiser/enabled', True)
            shoot('pt', args.pt_rounds + 4)
        except Exception:
            report['passes']['pt'] = {'error': traceback.format_exc()[-800:]}
    report['status'] = 'ok'
except Exception:
    report['status'] = 'failed'
    report['error'] = traceback.format_exc()
finally:
    report['wall_s'] = round(time.time() - START, 1)
    (OUT / 'hero_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print('HERO_RENDER_DONE', report.get('status'), flush=True)
    try:
        app.close()
    except Exception:
        pass
