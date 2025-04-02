"use strict";

const params = {
//    mesh : "data/batch/Batch3_18-12-2023/11-10.stl",
    mesh : "indiana/onedrive/23-ETW-90 (Project 1) - PM/BATCH 4/1000 LowerJawScan.stl",
    experiment : "DeepSDFModels/16",
    variance : 0.000001,
    nearSurfaceSamplingRatio : 1,
    yMin : -0.5
};

console.clear();
const { desk, qx, THREE } = window;
let original, cut, reconstruction;
const viewer = new desk.THREE.Viewer();
const container = new qx.ui.container.Composite();
container.setLayout( new qx.ui.layout.VBox( 5 ) );
viewer.getWindow().addAt( container, 0 );

const container2 = new qx.ui.container.Composite();
container2.setLayout( new qx.ui.layout.VBox( 5 ) );
viewer.add( container2, { left : 10, bottom : 10 } );
const showBoth = new qx.ui.form.CheckBox( "show both" );
container2.add( showBoth );
showBoth.addListener( "changeValue", updateVisibilities );
const switchView = new qx.ui.form.CheckBox( "switch" );
container2.add( switchView );
switchView.addListener( "changeValue", updateVisibilities );

const mesh2NPZ = new desk.Action( "mesh2NPZ" );
container.add( mesh2NPZ, { flex : 1 } );
const inputMesh = mesh2NPZ.getForm( "inputMesh" );
inputMesh.addListener( "changeValue", clear );
inputMesh.setValue( params.mesh );
mesh2NPZ.setParameters( { variance : params.variance, nearSurfaceSamplingRatio : params.nearSurfaceSamplingRatio,
    yMin : params.yMin  } );

const specsView = new qx.ui.form.TextArea("");
//specsView.setWrap( true );
specsView.setReadOnly( true )
const reconstruct = new desk.Action( "DeepSDFReconstruction" );
container.add( reconstruct, { flex : 1 } );
container.add( specsView, { flex : 1 } );
reconstruct.connect( "inputDistances", mesh2NPZ, "distance.npz" );
reconstruct.getForm( "experiment" ).addListener( "changeValue", onChangeExperiment );
reconstruct.setParameter( "experiment", params.experiment );
reconstruct.addListener( "actionUpdated", afterReconstruction );



async function onChangeExperiment() {
    const dir = reconstruct.getForm( "experiment" ).getValue();
    const specs = JSON.parse( await desk.FileSystem.readFileAsync( dir + "/specs.json" ) );
    specsView.setValue( "specs.json : \n" + JSON.stringify( specs, null, 2 ) );
}


const download = new qx.ui.form.Button( "Download reconstruction" );
download.addListener( "execute", () => window.ACVD.downloadOBJ( reconstruction,
    `${mesh2NPZ.getForm("inputMesh").getValue().split( "\\").pop().split(".")[ 0 ]}.obj` ));
container.add( download );


function updateVisibilities() {

    if ( !reconstruction ) return;
    const meshes = switchView.getValue() ? [ reconstruction, original ] : [ original, reconstruction ];
    reconstruction.material.color.set( "yellow" );
    const [ m1, m2 ] = meshes;
    m1.material.opacity = 1;
    m1.material.transparent = false;
    m1.visible = true;
    m1.renderOrder = 1;
    m2.material.opacity = 0.2;
    m2.material.transparent = true;
    m2.visible = showBoth.getValue();
    m2.renderOrder = 2;
    viewer.render();

}

async function clear() {

    viewer.removeAllMeshes();
    original = await viewer.addFileAsync( inputMesh.getValue() );
    reconstruction = null;

}

async function afterReconstruction() {

    await clear();
    reconstruction = await viewer.addFileAsync( reconstruct.getOutputDirectory() + "/mesh.ply" );
    updateVisibilities();

}