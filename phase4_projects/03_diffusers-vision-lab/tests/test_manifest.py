from diffusers_lab.manifest import new_run_id

def test_new_run_id_contains_task_and_seed():
    rid = new_run_id("txt2img", 42)
    assert "txt2img" in rid
    assert "seed42" in rid
