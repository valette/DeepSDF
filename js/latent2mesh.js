"use strict";
console.clear();

const { desk, qx, THREE } = window;

const params = {

    modelDir : "DeepSDFModels/56",
    csvSource : "DeepSDFModels/56/CSV/1ere_PM_Mand_(1)_modif.csv",
    csvTarget : "DeepSDFModels/56/CSV/1ere_PM_sup_(12).csv",
    interpolationSteps : 10,
    resolution : 64

};

desk.URLParameters.parseParameters( params );
const viewer = new desk.THREE.Viewer();
if ( desk.auto ) viewer.fillScreen();
const container = new qx.ui.container.Composite();
container.setLayout( new qx.ui.layout.VBox( 5 ) );
container.setWidth( 200 );
viewer.getWindow().addAt( container, 0 );
const modelDir = new desk.FileField( params.modelDir );
container.add( new qx.ui.basic.Label( "Model directory:") );
container.add( modelDir );

const csvSource = new desk.FileField( params.csvSource );
container.add( new qx.ui.basic.Label( "Source CSV file:") );
container.add( csvSource );
const csvTarget = new desk.FileField( params.csvTarget );
container.add( new qx.ui.basic.Label( "Target CSV file:") );
container.add( csvTarget );

const interpolationSteps = new desk.FileField( "" + params.interpolationSteps );
container.add( new qx.ui.basic.Label( "Interpolation steps:") );
container.add( interpolationSteps );
const resolution = new desk.FileField( "" + params.resolution );
container.add( new qx.ui.basic.Label( "Resolution:") );
container.add( resolution );

const reconstructButton = new qx.ui.form.Button( "Reconstruct");
reconstructButton.addListener( "execute", reconstruct );
container.add( reconstructButton );
const snapshot = async function () {
    viewer.snapshot( { path : "data/snapshots/frame" + animator.getFrame().toString().padStart( 4, "0" ) + ".png" } );
};
const animator = new desk.Animator( viewer.render.bind( viewer ),
    { snapshotCallback : snapshot } );
animator.getChildren()[ 0 ].setVisibility( "excluded" );
animator.setLoop( false );

async function reconstruct() {

    container.setEnabled( false );
    viewer.removeAllMeshes();
    animator.clearObjects();
    animator.setVisibility( "excluded" );
    const csv1 = await readCSV( csvSource.getValue() );
    const csv2 = await readCSV( csvTarget.getValue() );
    const steps = parseFloat( interpolationSteps.getValue() );
    const arr = [];
    for ( let i = 0; i <= steps; i++ ) arr.push( i );

    const promises = arr.map( async step => {

        const ratio = step / steps;
        const interpolated = csv1.map( ( v, i ) => ( 1 - ratio ) * v + ratio * csv2[ i ] );
        const csv = await desk.FileSystem.writeCachedFileAsync( "csv" + ratio + ".csv",
            interpolated.join( "," ) );

        const reconstruct = await desk.Actions.executeAsync( {
            experiment : modelDir.getValue(),
            action : "latent2mesh",
            csv,
            resolution : resolution.getValue()
        } );

        return await viewer.addFileAsync ( reconstruct.outputDirectory +'/mesh.ply',
            { label : "mesh" + step });
        
    } );

    const meshes = await Promise.all( promises );
    for( let mesh of meshes ) animator.addObject( mesh );
    animator.setFrame( 0 );
    animator.setVisibility( "visible" );
    viewer.add( animator, { right : 10, bottom : 10 } );
    container.setEnabled( true );

}

async function readCSV( file ) {
    const txt = await desk.FileSystem.readFileAsync( file );
    return txt.split( ',' ).map( parseFloat ).filter( n => !isNaN( n ) );
}

reconstruct().catch( console.warn );
