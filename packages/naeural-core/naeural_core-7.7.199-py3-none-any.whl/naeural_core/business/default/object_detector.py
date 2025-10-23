from naeural_core.business.base.cv_plugin_executor import CVPluginExecutor as BasePlugin


_CONFIG = {
  **BasePlugin.CONFIG,
  'PROCESS_DELAY': 0,

  "AI_ENGINE": "lowres_general_detector",
  "COLOR_TAGGING": True,
  "DEBUG_DETECTIONS": False,

  'VALIDATION_RULES': {
    **BasePlugin.CONFIG['VALIDATION_RULES']
  },
}


class ObjectDetectorPlugin(BasePlugin):
  """
  Demo plugin for checking the video object detection.
  """

  def _draw_witness_image(self, img, inferences, **kwargs):
    """
    Draw the inferences on the image.
    """
    for inference in inferences:
      box_tlbr = inference[self.consts.TLBR_POS]
      lbl = inference[self.consts.TYPE]
      lbl += f" | {inference.get(self.consts.COLOR_TAG)}"

      img = self._painter.draw_detection_box(
        image=img,
        top=box_tlbr[0],
        left=box_tlbr[1],
        bottom=box_tlbr[2],
        right=box_tlbr[3],
        label=lbl,
        prc=inference[self.consts.PROB_PRC],
        color=self.consts.DARK_GREEN
      )
    return img

  def process(self):
    instance_inferences = self.dataapi_image_instance_inferences()
    payload = None

    if self.cfg_debug_detections:
      self.P(f"Currently found {len(instance_inferences)} inferences.")

      if len(instance_inferences) > 0:
        self.P(f'inference keys: {instance_inferences[0].keys()}')
    # endif debug_detections

    payload_kwargs = {
      "objects": instance_inferences,
    }

    if self.cfg_demo_mode:
      np_witness = self.get_witness_image(
        draw_witness_image_kwargs={
          "inferences": instance_inferences,
        }
      )

      payload_kwargs["img"] = np_witness
    # endif demo_mode
    # The timestamp will be added to the payload in the base plugin.
    payload = self._create_payload(**payload_kwargs)
    return payload


